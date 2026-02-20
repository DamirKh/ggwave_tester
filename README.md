# ggwave Noise Resistance Tester
A Python tool for testing the noise resistance of the ggwave library under various Signal-to-Noise Ratio (SNR) conditions.
### Features
Tests multiple ggwave protocols (Fast, Normal, Robust)
Simulates white Gaussian noise at different SNR levels (in dB)
Provides clean, summarized results with statistics
Compares protocol performance under noisy conditions
### Requirements
Python 3.7+
ggwave Python library
NumPy
## Installation
```commandline
pip install -r requirements.txt
```


## Usage
Run the test script:
```commandline
python main.py
```


### The script will:
Encode a test message using different protocols
Add noise at various SNR levels (from 40 dB to -10 dB)
Attempt to decode the noisy signal
Display a summary table showing which protocols work at which noise levels
Write .wav files to check noise
