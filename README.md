hose: an attempt to unify unix pipeline and python
==================================================

### note
This is an experimental software.

### hose

  1. We should have some ways of coupling programs like
     garden hose--screw in another segment when it becomes when
     it becomes necessary to massage data in another way.
  -- Doug McIlroy

### an example
This pipeline implements a little spider that crawls github api to 
report the most prolific followers of nodejs-related repos.

        import hose as h

        p=h.vals(['https://api.github.com/legacy/repos/search/nodejs']) \
            >> h.fetch() \
            >> h.jq('-M', '-r', '.repositories[] | "https://api.github.com/repos/\(.owner)/\(.name)/subscribers"') \
            >> h.head(50) \
            >> h.fetch() \
            >> h.jq('-M', '-r', '.[].login') \
            >> h.hist() \
            >> h.fmt("{1}\t{0}")\
            >> h.out()
        p.run()

        21	equus12
        19	hcilab
        14	sequoiar
        8	sinopower
        7	gustavpursche
        6	Yangpu

### The goal: pipelien equivalence

Given this pipeline in unix shell:

   foo  | bar  | baz 

we should have this in python:

   foo >> bar >> baz 

Any segment should be easily swappable between the python and shell version.
Command foo should be callable from python. Conversely python function that 
implements a segment should be callable as a command.

### some ideas
* data stream processor as fundamental unit of software construction
  * prototype with unix pipeline
  * bake into a single python program
* blend unix pipe and python code
  * should be able to go back and forth
* unify access to various data sources: db, web, json, log..

### todo:
* functional
  current processors could be replaced by a map class 
  that takes a data processing function.

* forking and joining the streams
  for stream of pairs, allow pair of processors: 
  >> proc(passthru(), fmt())
  >> proc(passthru(), fetch())
  alternatively, apply the proc to a selected element, leaving other as is:
  >> sel(index=1).fmt(...) >> sel(index=1).fetch() >> out()
