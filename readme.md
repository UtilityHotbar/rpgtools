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
# Returns random entry from table
myTable.table_interact()
# Interactive table CLI (Use !help for more options)
```