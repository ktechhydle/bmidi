<img src="assets/bmidi.png">

`bmidi` is a Python-based automatic keyframing tool for MIDI data, allowing users to create smooth MIDI-driven animations in Blender.

## Installing `bmidi`

`bmidi` is not currently available as a full Blender addon, so creating a clone of this repository is necessary for usage.

1. Clone The Repo

Clone this repository into the desired folder with:

```sh
git clone https://github.com/ktechhydle/bmidi.git
```

2. Install The Python Requirements

Find the Blender Python executable's path using `bpy.app.binary_path` in the console, then input the following into a new terminal (located in this repositories root):

```sh
'<your blender python path>' -m pip install -r requirements.txt
```

You may have to ensure `pip` actually exists by first using:

```sh
'<your blender python path>' -m ensurepip
```

Then upgrading it with:

```sh
'<your blender python path>' -m pip install --upgrade pip
```

3. Run `main.py`

Create a new Blender project inside the root of this repository, and open the `main.py` file inside the "Script" tab. Run the file with `Alt-P` or use the run button located right next to the file name, and you're done!

## Using `bmidi`

`bmidi`'s user interface is just a single panel with controls for frame generation.

- You can add or remove items with the "+" or "-" buttons located in the top right of the panel.
- Items can either be **instrument controllers** or **composition controllers**, depending on what you select in "Type". 
- Instruments represent individual objects that can be controlled by an entire midi file, or a specific note in the midi file. 
- Compositions represent a collection of instruments that map notes to object names. For example, an object named `Key_25` might be hit whenever note 25 is hit in the midi file. Compositions are great for things like xylophones, pianos, marimbas, etc. where you need to control multiple objects all at once based on notes. The format for composition objects is `<object_prefix>_<note_number>`.

Clicking "Generate Keyframes" will set the timeline to `-1`, reset the animation data for all instrument and composition objects, then generate the frames. _Generation can be slow with large midi files, optimizations will come in future commits._
