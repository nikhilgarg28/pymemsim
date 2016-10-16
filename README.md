# pymemsim
pymemsim tries to simulate memory lookups on modern processors.

Many interesting programs are often bottlenecked on just the memory bandwidth.
In such cases, processor is just waiting for memory almost all the time. This
is a direct result of Von Neumann Bottleneck and is very fundamental to the
ubiquitous design of mainstream computers.

Modern processors have been trying to side-step this bottleneck by employing
many harware abstractions like processor caches. Unfortunately, it's not easy
to write tight code that fully utilizes these abstractions. On top of this,
Unix adds a layer of virtual memory which makes it even harder to argue about
memory performance. The goal of pymemsim is to make it easy to understand
memory bandwidth bottlenecks in various algorithms of interest.

Pymemsim simulates the process of reading data on simple but modern processors:
* Supports multiple hieararchical caches with various access latencies
* Supports write-back/write-through caches
* Supports associative caches
* Supports tracking all cache/memory events as they happen

I also hope to add the following to pymemsim over time:
* Support for virtual memory (TLB, Page Tables...)
* Ability to simulate operations on Arrays and structs.
* Some examples where a tool like pymemsim can help make the algorithm more
  efficient.


Please note that pymemsim is way too simplistic to come anywhere close to
correctly simulate modern processor hardware. That's not even the goal here.
Instead, the goal is to develop broad intutition on the interaction of an
algorithm with various layers of memory lookup abstraction.
