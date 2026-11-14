# Terrorizer
![Example Image](terrorizerv0.png)


Terrorizer is a Python package is designed to streamline the process of **organizations' names disambiguation (i.e. entity linking)** using a combination of **natural language processing** and **network theory techniques**. It provides an integrated solution for harmonizing names variants, exploiting four different stages:
- names preprocessing
- (optional) knowledge augmentation: augmenting data with our growing knowledge bases in company names to improve the precision of the results
- matching stage
- community detection through network theory


# Important links
- Download our knowledge base composed by web crawled company information including correct spelling as well as companies websites: [here](https://drive.google.com/file/d/1gdEasszoW1v6dWkelnSh4VJYoCX7z3ed/view?usp=sharing "Optional title")
- (Working) paper:
- Colab tutorial

# Installation
```bash
pip install terrorizer
```

# Usage
```bash

from terrorizer import terrorizer_disambiguator

results = terrorizer_disambiguator(df, knowledge_base_path='./knowledge_base_duckduck24v2.csv', column_name='names_to_disambiguate') ##using our knowledge base
results = terrorizer_disambiguator(df, column_name='names_to_disambiguate') #without using our knowledge base
```
# Contributing

Contributions are welcome! If you encounter any issues or have suggestions for improvement, please create a new issue or submit a pull request

# License

This project is licensed under the GNU General Public License.

# Package Maintainer(s)

Grazia Sveva Ascione (graziasveva)
