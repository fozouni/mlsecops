# Stream Processing with Quix

[toc]

## Requirements of this project

```bash
pip install quixstreams faker kafka-python
```



## Some Links

🚀 https://www.kai-waehner.de/blog/2023/05/28/quix-streams-stream-processing-with-kafka-and-python/

🚀 https://github.com/faust-streaming/faust

🚀 https://faust-streaming.github.io/faust/

🚀 https://quix.io/docs/quix-streams/introduction.html

🚀 https://github.com/quixio/quix-streams



## Tutorials

🚩 https://quix.io/docs/quix-streams/tutorials/word-count/tutorial.html

🚩 https://quix.io/docs/quix-streams/tutorials/anomaly-detection/tutorial.html



## Read more about `.current()` and `.final()`

https://quix.io/docs/quix-streams/windowing.html#updating-window-definitions

**Here with two record, I am going to explain the `.current()` behavior to you, pay attention to it:**

**At time T0: .current()**:
When the record with a temperature of 90 arrives, the alert is triggered immediately because the mean of the current window (which only contains that record) is 90, meeting the threshold.

**At time T1: .final()**:
When the next record with a temperature of 85 arrives, the mean is recalculated to 87.5, and no alert is triggered because it falls below the threshold.
