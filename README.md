# comics-splitter
Comics Splitter is a Python script that cut comic strip or manga page in panels. This allow the reader to have a better reading experience on small devices like ereader, smartphone or tablet 

## Dependencies
* Python3
* Pillow

## Usage
```python3 comics_splitter.py -i <inputDir> -o <outputDir>

Options:
    -r, --rotate : enable rotation to always have a portrait page (very usefull on E-reader)
    -d, --diago : enable diagonal split (longer processing)
    -s, --sort : smart sort on files name (Windows sort)
    -h, --help : print help
    --draw : only draw cut area
```

## Example
This is an example with 2 manga's pages.
**In** :

![manga1](https://img4.hostingpics.net/pics/700264index191.jpg)
![manga2](https://img4.hostingpics.net/pics/608616index571.jpg)

**Ou** (The red polygon show the cut area) :

![manga1cut](https://img4.hostingpics.net/pics/783604draw2100.png)
![manga2cut](https://img4.hostingpics.net/pics/812133draw2300.png)

## TODO:
* add vertical split
* add option in command line
* improve speed of diagonal cut !
* add black (or other color) border support
