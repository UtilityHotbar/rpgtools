# Rpgtools

A collection of tools for rpgs.

## Modules
`main.py`: Primary functionality. Includes a dice roller and menu generator.

**Basic Usage**

```python
import rpgtools.main
print(rpgtools.main.roll('1d6'))
# Returns a random value from 1 to 6
myChoice = rpgtools.main.generate_menu(['Apple', 'Pear', 'Orange'])
# Creates a menu with three options then returns the index
```

`table_process.py`: Module for processing random tables. Tables use a file format similar to Inspiration Pad Pro 3. Example tables are included in the `text` directory

**Basic Usage**

```python
import rpgtools.table_process
myTable = rpgtools.table_process.Table('path/to/table.txt')
myTable.table_fetch('TableHeader')
# Returns random entry from sub-table with header TableHeader
myTable.table_interact()
# Interactive table CLI (Use !help for more options)
```

## Applications

`lang_gen.py`: Creates constructed languages and translates sentences into them from English. Uses Peter de Vocht's [Enhanced Subject Verb Object Extraction](https://github.com/peter3125/enhanced-subject-verb-object-extraction) for translation purposes.

`mini_dungeon.py`: Simulation of a dungeon master and a very basic dungeon crawler.