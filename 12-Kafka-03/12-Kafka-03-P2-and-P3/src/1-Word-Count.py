from collections import Counter
from quixstreams import Application

app = Application(
    broker_address="localhost:9092,localhost:9094,localhost:9096",
    consumer_group="product_review_word_counter",
    auto_offset_reset="earliest",
)

product_reviews_topic = app.topic(name="product_reviews")

word_counts_topic = app.topic(name="product_review_word_counts")


def tokenize_and_count(text):
    return list(Counter(text.lower().replace(".", " ").split()).items())

'''
text = "Hello world. Hello everyone."

text.lower()
  Result: "hello world. hello everyone."
  
text.lower().replace(".", " ")
  Result: "hello world  hello everyone "
  
text.lower().replace(".", " ").split()
  Result: ['hello', 'world', 'hello', 'everyone']

word_counts = Counter(['hello', 'world', 'hello', 'everyone'])
  Result: Counter({'hello': 2, 'world': 1, 'everyone': 1})


list(word_counts.items())
  Result: [('hello', 2), ('world', 1), ('everyone', 1)]
'''

def should_skip(word_count_pair):
    word, count = word_count_pair
    return word not in ["i", "a", "we", "it", "is", "and", "or", "the"]


sdf = app.dataframe(topic=product_reviews_topic)

sdf = sdf.apply(tokenize_and_count, expand=True)

'''
expand=True #Result:  ('hello', 2)  =====> 'hello' is a key and 2 is a value.
                      ('world', 1)
                      ('everyone', 1)
'''
sdf = sdf.filter(should_skip)

sdf = sdf.to_topic(word_counts_topic, key=lambda word_count_pair: word_count_pair[0])

sdf.print()

if __name__ == "__main__":
    app.run()
