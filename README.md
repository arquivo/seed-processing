# seed-processing
Script used to process urls to decide whether or not they are of good quality to collect

http://www.vivapraia.com/ is a good example of the difficulty of doing this type of analysis since the same URL can be attacked by different persons or the first attacker can change it to profit from other way. It is possible to see each versions preserved in Arquivo.pt from this website and how it changes over time and even today.

Others outliers:
Example:
http://22blog.com
http://casteleiro-sabugal.new.fr

### Setup

```
git clone https://github.com/arquivo/seed-processing.git
cd seed-processing
pip install --upgrade virtualenv
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
wget https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin
``` 

### Run

```
python process_seeds.py
```

### Parameters

<pre>
-f or --file        --> Localization of the file
-b or --bin         --> Localization of the binary file of firefox
-p or --path        --> Localization of the geckodriver file of firefox
-l or --lines       --> Number of lines in each temporary file
</pre>

### Example

Run the example:

```
python process_seeds.py -f seeds_test.txt -l 5 
```
### Authors

- [Pedro Gomes](pedro.gomes.fccn@gmail.com)
