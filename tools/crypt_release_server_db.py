"""Stop-on-error mysql transport and canonical-SQL-derived pilot transaction.

No stored routines are installed. Only the pinned canonical INSERT/SELECT
clauses are compiled to unconditional INSERTs, inside one explicit transaction.
The interactive transport lets the filesystem journal fsync exact rows before
COMMIT can be sent. Losing the connection before COMMIT rolls back InnoDB.
"""
import re
import subprocess

from crypt_release_client import require, sha

SQL_HASHES = {
    'turtle_wow_maps.sql': '5daa184663ffd8682668948096c800151b8888ed80a5935d781b918ea417d156',
    'turtle_wow_crypt_access.sql': 'f60861d4aebae154d471de0f1bad8b10bb84d81de218e9554b4829c4dbf6e109',
}
OWNED = {
    'instance_template': ('map', '800'),
    'areatrigger': ('entry', '900800,900801'),
    'areatrigger_teleport': ('ID', '900800,900801'),
    'gameobject_template': ('entry', '900800,900801'),
    'gameobject': ('guid', '900800,900801'),
    'dungeon_access_template': ('id', '124'),
}


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}', value),
            'Invalid database identifier')
    return value


def compile_sql(sources):
    result = []
    for name in ('turtle_wow_maps.sql', 'turtle_wow_crypt_access.sql'):
        raw = sources[name]
        require(sha(raw) == SQL_HASHES[name], f'Canonical SQL hash mismatch: {name}')
        text = raw.decode('utf-8')
        matches = re.findall(r'INSERT INTO `([a-z_]+)`\s*\(([^;]+?)\)\s*SELECT\s+(.+?)\s+WHERE NOT EXISTS', text, re.S)
        require(len(matches) == (1 if name == 'turtle_wow_maps.sql' else 9), 'Unsupported canonical SQL')
        for table, columns, values in matches:
            require(table in OWNED and re.fullmatch(r'[\s`,A-Za-z0-9_]+', columns), 'Unsupported INSERT')
            result.append((table, re.findall(r'`([^`]+)`', columns),
                           f'INSERT INTO `{table}` ({columns}) VALUES ({values});'))
    require(len(result) == 10, 'Expected ten pilot rows')
    return result


class Database:
    def __init__(self, database, login_path, defaults_file=None, mysql='mysql'):
        self.database = identifier(database)
        self.command = [mysql]
        if defaults_file:
            self.command.append('--defaults-extra-file=' + str(defaults_file))
        if login_path:
            require(re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}', login_path), 'Invalid login path')
            self.command.append('--login-path=' + login_path)
        self.command += ['--batch', '--raw', '--skip-column-names', '--unbuffered',
                         '--default-character-set=utf8mb4', '--database=' + self.database]

    def query(self, sql):
        p = subprocess.run(self.command, input=sql, text=True, capture_output=True)
        require(p.returncode == 0, 'mysql failed: ' + p.stderr.strip())
        return p.stdout.splitlines()

    def server_identity(self):
        rows = self.query('SELECT @@server_uuid;')
        require(len(rows) == 1 and re.fullmatch(r'[0-9a-fA-F-]{36}', rows[0]),
                'A stable MySQL server UUID is required')
        return rows[0].lower()

    def schema(self, compiled):
        needed = {table: set(cols) for table, cols, _ in compiled}
        for table, cols, _ in compiled:
            needed[table].update(cols)
        rows = self.query('SELECT TABLE_NAME,COLUMN_NAME FROM information_schema.COLUMNS '
                          f"WHERE TABLE_SCHEMA='{self.database}' ORDER BY TABLE_NAME,ORDINAL_POSITION;")
        columns = {}
        for line in rows:
            table, column = line.split('\t')
            columns.setdefault(table, []).append(column)
        for table, names in needed.items():
            require(names <= set(columns.get(table, [])), f'Incompatible SQL columns: {table}')
        engines = self.query('SELECT TABLE_NAME,ENGINE FROM information_schema.TABLES '
                             f"WHERE TABLE_SCHEMA='{self.database}';")
        engine = dict(line.split('\t') for line in engines)
        require(all(engine.get(t) == 'InnoDB' for t in OWNED), 'Owned tables must use InnoDB')
        triggers = self.query('SELECT TRIGGER_NAME FROM information_schema.TRIGGERS '
                              f"WHERE TRIGGER_SCHEMA='{self.database}' AND EVENT_OBJECT_TABLE IN (" +
                              ','.join("'" + t + "'" for t in OWNED) + ');')
        require(not triggers, 'Triggers on owned tables are unsupported')
        return columns

    @staticmethod
    def snapshot_sql(columns):
        queries = []
        for table, (pk, ids) in OWNED.items():
            require(table in columns, f'Missing SQL table: {table}')
            args = ','.join('`' + c + '`' for c in columns[table])
            queries.append(f"SELECT '{table}', HEX(CAST(JSON_ARRAY({args}) AS CHAR)) FROM `{table}` "
                           f'WHERE `{pk}` IN ({ids}) ORDER BY `{pk}`;')
        return '\n'.join(queries)

    def snapshot(self, columns):
        return self.query(self.snapshot_sql(columns))

    def bindings(self):
        # These guards are intentionally stricter than the canonical reapply SQL.
        guards = [
            ('dungeon_access_template', 'map_id=800 AND id<>124'),
            ('dungeon_access_requirements', 'dungeon_access_id=124'),
            ('areatrigger_scripts', 'entry IN (900800,900801)'),
            ('areatrigger_tavern', 'id IN (900800,900801)'),
            ('areatrigger_involvedrelation', 'id IN (900800,900801)'),
            ('gameobject', 'id IN (900800,900801) AND guid NOT IN (900800,900801)'),
            ('map_dbc', "ID=800 OR Directory='KarazhanCrypt'"),
            ('areatable_dbc', 'ID=5086 OR ContinentID=800'),
            ('mapdifficulty_dbc', 'ID=756 OR MapID=800'),
            ('worldmaparea_dbc', 'ID=674 OR MapID=800 OR AreaID=5086'),
        ]
        for table, condition in guards:
            require(self.query(f'SELECT COUNT(*) FROM `{table}` WHERE {condition};') == ['0'],
                    f'SQL binding/overlay collision: {table}')

    def transaction(self, statements, columns, before, persist):
        """persist(snapshot) must durably record intent before COMMIT is sent."""
        process = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, bufsize=1)
        def exchange(sql):
            process.stdin.write(sql + "\nSELECT 'CRYPT_RELEASE_END';\n")
            process.stdin.flush()
            lines = []
            while True:
                line = process.stdout.readline()
                require(line, 'mysql transaction stopped: ' + '\n'.join(lines))
                line = line.rstrip('\n')
                if line == 'CRYPT_RELEASE_END':
                    return lines
                require(not line.startswith(('ERROR', 'Warning')), 'mysql transaction failed: ' + line)
                lines.append(line)
        try:
            exchange('SET NAMES utf8mb4; SET TRANSACTION ISOLATION LEVEL SERIALIZABLE; START TRANSACTION;')
            # Lock every owned range and recheck the exact preflight snapshot.
            for table, (pk, ids) in OWNED.items():
                exchange(f'SELECT `{pk}` FROM `{table}` WHERE `{pk}` IN ({ids}) FOR UPDATE;')
            require(exchange(self.snapshot_sql(columns)) == before, 'SQL changed after preflight')
            exchange('\n'.join(statements))
            snapshot = exchange(self.snapshot_sql(columns))
            persist(snapshot)
            exchange('COMMIT;')
            return snapshot
        finally:
            if process.poll() is None:
                process.stdin.close()  # EOF rolls back any uncommitted transaction.
                process.wait(timeout=30)
            process.stdout.close()


def deletes():
    return [f'DELETE FROM `{table}` WHERE `{pk}` IN ({ids});'
            for table, (pk, ids) in reversed(list(OWNED.items()))]
