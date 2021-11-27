# Estimating the Bot Population on Twitter via Random Walk Based Sampling

## Installation
Clone this repository and enter the directory `twitter-bot-population-estimator/` in your terminal.

At first, update your secret keys in the *secrets.py*.
- Create a [Twitter app](https://apps.twitter.com/) and get Twitter API keys from the "Keys and tokens" tab of your app properties.
  - You need API Key, API Key Secret, Access Token, Access Token and should assign them to `consumer_key`, `consumer_secret`, `access_token`, `access_token_secret` in the *secrets.py*.
- Create a [RapidAPI](http://rapidapi.com/) account, subscribe to [Botometer Pro](https://rapidapi.com/OSoMe/api/botometer-pro) and get the RapidAPI key.
  - [Basic (Free) Plan](https://rapidapi.com/OSoMe/api/botometer-pro/pricing) is sufficient for test use. This plan has a hard limit of 500 accounts per day for inquiries.
  - The easiest way to obtain the key is to visit [API endpoint page](https://rapidapi.com/OSoMe/api/botometer-pro/endpoints) and find "X-RapidAPI-Key" in the "Header Parameters". Put that value in `rapidapi_key` in the *secrets.py*.
  - See [Botometer Python API](https://github.com/IUNetSci/botometer-python) for details.

Also, you will need some Python packages installed. You can just run:
```
$ pip install -r requirements.txt
```
We verified that the program work properly with Python 3.9.1.

## Usage
```
$ bot_population_estimator.py {rw,bot} ...
```

There are two positional arguments:
1. [rw](#1-rw): perform random walk
2. [bot](#2-bot): calculate bot score and population with reading samplinglist/botscore file

### 1. rw
You can perform random walk from any public user.
```
$ python bot_population_estimator.py rw -i user_id
                                        (-r num_samples | --days num_days | --hours num_hours | --minutes num_minutes)
                                        [--calc-bot-ppl] [-t threshold_score] [-c num_cut_samples]
```
```
Required:
  -i user_id, --initial-user user_id
                        initial user id (64-bit integer)

One of following is required:
  -r num_samples, --samplesize num_samples
                        number of samples to collect
  --days num_days       sampling time [days]
  --hours num_hours     sampling time [hours]
  --minutes num_minutes
                        sampling time [minutes]

Optional:
  --calc-bot-ppl        calculate bot score simultaneously, and the bot population is output at the end.
  -t threshold_score, --threshold threshold_score
                        threshold to classify whether a user is bot (default is 0.95)
  -c num_cut_samples, --cut num_cut_samples
                        number of the first samples to be discarded (default is 0)
```

#### (a) Only sampling
For example, if you want to start a random walk from a *user 12* and want *100 samples*, run:
```
$ python bot_population_estimator.py rw -i 12 -r 100
```
-*samplinglist*.txt will be created in outputs/. (See [Output Format](#output-format) for details.)

You can also specify sampling time instead of sample size.
For example, when you want to collect samples for 3 days, run:
```
$ python bot_population_estimator.py rw -i 12 --days 3
```
You may get around 1,400-1,500 samples in 24 hours.

> 💡 You can obtain user id from the screen name (user name following @) by running `$ python get_id_screen_name.py <screen_name>` in this directory.

#### (b) Sampling and estimation 👈 Recommended
You can also use the optional flag `--calc-bot-ppl` to get the bot score for each sampled user at the same time.
```
$ python bot_population_estimator.py rw -i 12 -r 100 --calc-bot-ppl
```
-*botscore*.txt and -*est*.txt will be saved in outputs/ as well. (See [Output Format](#output-format) for details.)

You can change threshold of the bot score for binary classification with flag `-t`, and discard a specified number of the first samples with flag `-c`.
For example,
```
$ python bot_population_estimator.py rw -i 12 -r 100 --calc-bot-ppl -t 0.9 -c 10
```
gives estimates by classifying the bots with a threshold of *0.9* and discarding the *first 10 samples*. Practically, it is desirable to discard the first some samples to exclude the dependency of the initial node.

### 2. bot
You can obtain estimates with reading an existing file.
```
$ python bot_population_estimator.py bot -f file_path [-t threshold_score] [-c num_cut_samples]
```
```
Required:
  -f file_path, --file file_path
                        path to -samplinglist/-botscore file

Optional:
  -t threshold_score, --threshold threshold_score
                        threshold to classify whether a user is bot (default is 0.95)
  -c num_cut_samples, --cut num_cut_samples
                        number of the first samples to be discarded (default is 0)
```

#### (a) From sampling list
If you specify the -*samplinglist*.txt file, bot score will be calculated for each node (saved as -*botscore*.txt) and estimates of the bot population will be shown (saved as -*est*.txt). (See [Output Format](#output-format) for details.)
```
$ python bot_population_estimator.py bot -f outputs/YYYY-mm-dd-HH-MM-SS-initialXXXX-samplesizeZZZZ-samplinglist.txt
Read outputs/YYYY-mm-dd-HH-MM-SS-initialXXXX-samplesizeZZZZ-samplinglist
Bot population: 0.0
```

> 💡 Please note that if you specify a file containing more than 500 samples, you may exceed Botometer's free usage limit.
If the limit on the number of account inquiries is exceeded, our program will record -1 as the bot score.

#### (b) From bot score
If you specify the -*botscore*.txt file, estimates of the bot population will be shown (saved as -*est*.txt, see [Output Format](#output-format) for details) with using the already calculated scores.
You can also change threshold of the bot score for binary classification with flag `-t`, and discard a specified number of the first samples with flag `-c`.

For example, if you want to get estimates by classifying bot and non-bot with threshold *0.9* and discarding *first 1000 samples*, run:
```
$ python bot_population_estimator.py bot -f outputs/YYYY-mm-dd-HH-MM-SS-initialXXXX-samplesizeZZZZ-botscore.txt -t 0.9 -c 1000
Read outputs/YYYY-mm-dd-HH-MM-SS-initialXXXX-samplesizeZZZZ-botscore
Bot population: 0.0
```

### Output Format
Results will be saved in *outputs/* directory as text files.
- **Samples**: r-th row in -*samplinglist*.txt contains:
  ```
  <r-th sample's user id> <number of r-th sample's followers> <number of r-th sample's friends> <size of union set of r-th sample's followers and friends>
  ```
- **Bot score**: r-th row in -*botscore*.txt contains:
  ```
  <r-th sample's user id> <r-th sample's bot score>
  ```
  Bot score here is a conditional probability that accounts with a score equal to or greater than this are automated.
- **Estimates**: r-th row in -*est*.txt indicates estimated bot population using 1st to r-th samples.
  If you have specified that the first n samples are to be discarded (by the `-c` flag), then the results from the first one excluding them will be displayed.

<!-- ## Reference
```
@inproceedings{fukuda2021,
    title = {Estimating the Bot Population on {Twitter} via Random Walk Based Sampling},
    author = {Fukuda, Mei and Nakajima, Kazuki and Shudo, Kazuyuki},
    year = {2021}
}
``` -->