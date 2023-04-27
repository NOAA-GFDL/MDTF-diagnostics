```mermaid
  flowchart TD
    rtconfig[/runtime config file/]-->fw[framework]
    fw[Framework]-->translateyn{Variable\n Translation?}
    translateyn-- Yes -->queryfieldlist[Query fieldlist for POD vars]
    fieldlist[/Variable\n Fieldlist/]-->queryfieldlist
    queryfieldlist-->querycatvar[Query ESM Intake catalog\n for POD vars]
    cat1[/ESM intake catalog/]-->querycatvar
    podset[/POD\n settings file/]-->querycatvar
    querycatvar-->dotranslate[Translate data]
    dotranslate-->adddf[Save trans var\n info to dataframe]
    adddf-->movefilesyn{Move input data?}
    translateyn-- No-->querycatvarnot[Query catalog for POD vars]
    podset-->querycatvarnot
    cat1-->querycatvarnot
    querycatvarnot-->adddf2[Save POD data subset\n to dataframe]
    adddf2-->movefilesyn
    movefilesyn-- Yes-->querycatfiles[Query catalog file paths]
    cat1-->querycatfiles
    querycatfiles-->movefiles[Move input data\n to workdir]
    movefiles-->moddf[Create/update data frame\n with workdir file paths]
    movefilesyn-- No -->ppyn{Do PP?}
    moddf-->ppyn
    ppyn-- No-->newcat[Write new catalog\n with updated POD data info]
    ppyn-- Yes-->dopp[level extraction\n unit conversion\n ... ]
    dopp-->writeppfiles[Write PP files to workdir]
    writeppfiles-->newcat
    newcat-->cat2[/New ESM Intake catalog\n with POD-specific data/]
```
