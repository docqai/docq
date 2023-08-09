# Gcs Loader

This loader parses any file stored on Gcs.

All files are temporarily downloaded locally and subsequently parsed with `SimpleDirectoryReader`. Hence, you may also specify a custom `file_extractor`, relying on any of the loaders in this library (or your own)!

> Gcs loader is based on `OpendalReader`.

## Usage

```python
from llama_index import download_loader

OpendalGcsReader = download_loader("OpendalGcsReader")

loader = OpendalGcsReader(
    bucket='bucket',
    path='path/to/data/',
    endpoint='[endpoint]',
    credentials='[credentials]',
)
documents = loader.load_data()
```

Note: if `credentials` is not provided, this loader to try to load from env.

---

This loader is designed to be used as a way to load data into [LlamaIndex](https://github.com/jerryjliu/gpt_index/tree/main/gpt_index) and/or subsequently used as a Tool in a [LangChain](https://github.com/hwchase17/langchain) Agent. See [here](https://github.com/emptycrown/llama-hub/tree/main) for examples.
