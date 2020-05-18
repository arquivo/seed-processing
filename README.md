# seed-processing
Script used to process urls to decide whether or not they are of good quality to collect

http://www.vivapraia.com/ is a good example of the difficulty of doing this type of analysis since the same URL can be attacked by different persons or the first attacker can change it to profit from other way. It is possible to see each versions preserved in Arquivo.pt from this website and how it changes over time and even today.

### Setup

```
git clone https://github.com/arquivo/mergeWARCs.git
cd mergeWARCs
pip install --upgrade virtualenv
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```
### Run

```
python XXXX.py
```

### Parameters

<pre>
-f or --file        --> Localization of the file
-l or --lines       --> Number of lines in each temporary file
</pre>

### Example

Example and default parameters:

```
python 
```
### Authors

- [Pedro Gomes](pedro.gomes.fccn@gmail.com)
