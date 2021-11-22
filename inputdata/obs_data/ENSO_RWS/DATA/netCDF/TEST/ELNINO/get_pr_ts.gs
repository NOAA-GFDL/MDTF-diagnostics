***

   'reset'
   'reinit'


    prefix = '../../ELNINO/'
 
    var.1 = 'pr'
    var.2 = 'ts'

    undef = 1.1E+20

    i = 1
   while( i <= 2) 

    'sdfopen '%prefix'/'%var.i'.nc'

    'q file'
    line = sublin( result, 5) 
    x1 = 1
    x2 = subwrd( line, 3)
    y1 = 1
    y2 = subwrd( line, 6)
    t1 = 1 

     nameout = var.i'.out'

     'set gxout fwrite'
     'set fwrite  '%nameout

     'set x '%x1' '%x2
     'set y '%y1' '%y2

     'd const( '%var.i', '%undef', -u)'

     'disable fwrite'
     'close 1'

     i  = i + 1
    endwhile 

   
