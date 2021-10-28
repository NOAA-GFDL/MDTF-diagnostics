

General design principles
-------------------------


The received Python wisdom is to use "duck typing": instead of explicitly 
checking ``isinstance(obj, Duck)``, assume anything with a ``quack()`` method
will do the job. For large-scale projects this philosophy can be questioned, but
it's what we adopt here.




General code style
------------------

- We aim for 80 character width, but treat this as a guideline, since readability
  should come first. 

- For standard library imports, we prefer "import" rather than "import from". 