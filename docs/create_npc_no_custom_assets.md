## Create new NPC without custom assets

### 0. (optional) Create new displayid

* Create desired model using [WoW Model Viewer](https://code.google.com/archive/p/wowmodelviewer/downloads?page=6).
* Export model navigating: `File/Export Model/X3D`.
* Look for main .PNG texture file on exported folder, you can delete the rest.
* Open `<texture_file>.png` using [BLPLab](https://www.hiveworkshop.com/threads/blp-lab-v0-5-0.137599/).
* Save file `BLP2`,  `Compressed (DXTC)`, click on `Alpha channel -> Transparent 1 pixel border`.
* Add new entry to `CreatureDisplayInfo.dbc` and `CreatureDisplayInfoExtra.dbc` using [WDBXEditor-2.0.0](https://github.com/Mapache-Warmane2077/WDBXEditor-2.0.0/releases).
* Upload DBC files to `~/azerothcore/env/dist/bin/dbc`
* Add DBC files to MPQ in `DBFilesClient` folder.
* Add `texture_file.blp` to MPQ in `Textures/BackedNpcTextures` folder.
* Create new entry in `creature_model_info` table by duplicating similar NPC.

### 1. Create new NPC