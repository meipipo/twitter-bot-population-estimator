# Estimating the Bot Population on Twitter via Random Walk

### Installation
At first, update your secret keys in the *secrets.py*.
- Create a [Twitter app](https://apps.twitter.com/) and get Twitter API keys from the "Keys and tokens" tab of your app properties.
- Create a [RapidAPI](http://rapidapi.com/) account, subscribe to [Botometer Pro](https://rapidapi.com/OSoMe/api/botometer-pro) and get the RapidAPI key.
  - The easiest way to obtain the key is to visit [API endpoint page](https://rapidapi.com/OSoMe/api/botometer-pro/endpoints) and find "X-RapidAPI-Key" in the "Header Parameters".
  - See [Botometer Python API](https://github.com/IUNetSci/botometer-python) for details.

You will need some python packages installed. You can just run:
```
$ pip install -r requirements.txt
```

### Usage
```
$ bot_population_estimator.py {rw,bot} ...
```

There are two positional arguments:
- `rw`: perform random walk
- `bot`: calculate bot score and population with reading samplinglist/botscore file

#### rw
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
                        number of the first samples to be discarded
```

For example, if you want to start random walk from a *user 12* and want *100 samples*, run:
```
$ python bot_population_estimator.py rw -i 12 -r 100
```
Results will be saved in outputs/YYYY-mm-dd-HH-MM-SS-initial12-samplesize100-**samplinglist**.txt and outputs/YYYY-mm-dd-HH-MM-SS-initial12-samplesize100-**log**.txt.

You can also get bot scores for each sampled user at the same time with an optional flag `--calc-bot-ppl`. -**botscore**.txt and -**est**.txt will be saved in outputs/ as well. You can change threshold of the bot score for binary classification with flag `-t`, and discard a specified number of the first samples with flag `-c`.

#### bot
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
                        number of the first samples to be discarded
```

##### From sampling list
If you specify the -*samplinglist*.txt file, bot score will be calculated for each node (saved as -*botscore*.txt) and estimates of the bot population will be shown (saved as -*est*.txt).
```
$ python bot_population_estimator.py bot -f outputs/YYYY-mm-dd-HH-MM-SS-initialXXXX-samplesizeZZZZ-samplinglist.txt
Read outputs/YYYY-mm-dd-HH-MM-SS-initialXXXX-samplesizeZZZZ-samplinglist
Bot population: 0.0
```

##### From bot score
If you specify the -*botscore*.txt file, estimates of the bot population will be shown (saved as -*est*.txt) with using the already calculated scores. You can also change threshold of the bot score for binary classification with flag `-t`, and discard a specified number of the first samples with flag `-c`.

For example, if you want to get estimates with threshold *0.9* and discarding *first 1000 samples*, run:
```
$ python bot_population_estimator.py bot -f outputs/YYYY-mm-dd-HH-MM-SS-initialXXXX-samplesizeZZZZ-botscore.txt -t 0.9 -c 1000
Read outputs/YYYY-mm-dd-HH-MM-SS-initialXXXX-samplesizeZZZZ-botscore
Bot population: 0.0
```

<!-- ### Reference
```
@inproceedings{fukuda2021,
    title = {Estimating the Bot Population on {Twitter} via Random Walk},
    author = {Fukuda, Mei and Nakajima, Kazuki and Shudo, Kazuyuki},
    year = {2021}
}
``` -->