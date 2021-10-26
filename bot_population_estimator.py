import argparse
import botometer
import datetime
import numpy as np
import time
import tweepy

from secrets import consumer_key, consumer_secret, access_token, access_token_secret, rapidapi_key

# Global constants
filepath_dir = "outputs/"
filepath_ext = ".txt"
max_num_items = 5000  # Maximum ids retrieved per query
max_query_neighbor = 900  # Maximum number of query to select next node


class InvalidFilePathError(Exception):
    """Exception class to signal that the specified filepath has invalid format.
    """
    pass


class GetNeighborsError(Exception):
    """Exception class to signal that an error has occurred while getting neighbors.
    """
    pass


class SelectNeighborError(Exception):
    """Exception class to signal that public neighbor cannot be selected from neighbors.
    """
    pass


def get_twitter_api_instance():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.API(auth, wait_on_rate_limit=True, timeout=60)


def get_botometer_instance():
    twitter_app_auth = {
        'consumer_key': consumer_key,
        'consumer_secret': consumer_secret,
        'access_token': access_token,
        'access_token_secret': access_token_secret,
    }
    return botometer.Botometer(wait_on_ratelimit=True,
                               rapidapi_key=rapidapi_key,
                               **twitter_app_auth)


def write_to_file(filepath, s):
    f = open(filepath, 'a')
    f.write(s + "\n")
    f.close()


def get_followers_ids(api, id, log_file_path):
    try:
        followers_ids = tweepy.Cursor(
            api.followers_ids, id=id, cursor=-1).items(max_num_items)
        return list(followers_ids)

    except tweepy.error.TweepError as e:
        message = "TweepError: Error at getting %s's followers: %s" % (
            id, e.reason)
        write_to_file(log_file_path, message)
        time.sleep(3)
        raise GetNeighborsError(message)
    except:
        message = "Error at getting %s's followers." % id
        write_to_file(log_file_path, message)
        time.sleep(3)
        raise GetNeighborsError(message)


def get_friends_ids(api, id, log_file_path):
    try:
        friends_ids = tweepy.Cursor(
            api.friends_ids, id=id, cursor=-1).items(max_num_items)
        return list(friends_ids)

    except tweepy.error.TweepError as e:
        message = "TweepError: Error at getting %s's friends: %s" % (
            id, e.reason)
        write_to_file(log_file_path, message)
        time.sleep(3)
        raise GetNeighborsError(message)
    except:
        message = "Error at getting %s's friends." % id
        write_to_file(log_file_path, message)
        time.sleep(3)
        raise GetNeighborsError(message)


def choose_destination(api, v, neighbors, visit, log_file_path):
    found_next = False
    num_query = 0

    while not found_next:
        sampled_neighbor = np.random.choice(neighbors)

        if sampled_neighbor in visit:
            found_next = True
            next_v = sampled_neighbor
        else:
            num_query += 1
            try:
                protected = api.get_user(sampled_neighbor).protected
                if not protected:
                    found_next = True
                    next_v = sampled_neighbor
            except tweepy.error.TweepError as e:
                message = "TweepError: Error at selecting %s's neighbor: %s %s: " % (
                    str(int(v)), sampled_neighbor, e.reason)
                write_to_file(log_file_path, message)
            except:
                message = "Error at selecting %s's neighbor" % (
                    str(int(v)), str(sampled_neighbor))
                write_to_file(log_file_path, message)

            if num_query >= max_query_neighbor:
                message = "Maximun number of query to select neighbor exceeded."
                write_to_file(log_file_path, message)
                return None

    return next_v


def walk(api, v, samplinglist, friends_dict, followers_dict, neighbors_dict, visit, log_file_path, samplinglist_file_path):
    # Retrieve neighbors and record them with adding the previous node
    if v in visit:
        if len(samplinglist) > 0:
            prev_v = samplinglist[-1][0]
            v_neighbors_set = set(neighbors_dict[v]) | set([prev_v])
            neighbors_dict[v] = list(v_neighbors_set)
    else:
        write_to_file(
            log_file_path, "Try to get followers and friends of %s" % str(int(v)))

        # Get followers
        try:
            followers = get_followers_ids(api, v, log_file_path)
        except:
            # Go back to the previous node and re-select the next node
            if len(samplinglist) > 0:
                prev_v = samplinglist[-1][0]
                v = choose_destination(
                    api, prev_v, neighbors_dict[prev_v], visit, log_file_path)
                if v:
                    return walk(api, v, samplinglist, friends_dict, followers_dict, neighbors_dict, visit, log_file_path, samplinglist_file_path)
                else:
                    return None
            else:
                raise GetNeighborsError("Please re-select initial node.")

        # Get friends
        try:
            friends = get_friends_ids(api, v, log_file_path)
        except:
            # Go back to the previous node and re-select the next node
            if len(samplinglist) > 0:
                prev_v = samplinglist[-1][0]
                v = choose_destination(
                    api, prev_v, neighbors_dict[prev_v], visit, log_file_path)
                if v:
                    return walk(api, v, samplinglist, friends_dict, followers_dict, neighbors_dict, visit, log_file_path, samplinglist_file_path)
                else:
                    return None
            else:
                raise GetNeighborsError("Please re-select initial node.")

        # Save data to dict
        followers_dict[v] = followers
        friends_dict[v] = friends
        v_neighbors_set = set(followers_dict[v]) | set(friends_dict[v])
        # Add previous node to make sure the current node can chose the public node
        if len(samplinglist) > 0:
            prev_v = samplinglist[-1][0]
            v_neighbors_set.add(prev_v)
        neighbors_dict[v] = list(v_neighbors_set)

        # Mark v as visited
        visit[v] = 1

    # Add to sampling list
    samplinglist.append([v, len(followers_dict[v]), len(
        friends_dict[v]), len(neighbors_dict[v])])
    l = [str(n) for n in samplinglist[-1]]
    write_to_file(samplinglist_file_path, ' '.join(l))

    # Choose next node from neighbors
    next_v = choose_destination(
        api, v, neighbors_dict[v], visit, log_file_path)

    return next_v


def calculate_bot_score(bom, v, botscore_file_path):
    try:
        result = bom.check_account(v)
        if result['user']['majority_lang'] == 'en':
            cap = result['cap']['english']
        else:
            cap = result['cap']['universal']
        write_to_file(botscore_file_path, str(v) + " " + str(cap))
        return cap
    except:
        write_to_file(botscore_file_path, str(v) + " -1")
        return -1


def calculate_bot_population(rw_sequence, bot_labels, degrees, cut=0, est_file_path=""):
    total_inv_degree = []
    total_labeled_inv_degree = []
    est_0toi = []

    for i in range(len(rw_sequence)):
        v = rw_sequence[i]

        if i < cut:
            continue

        if i == cut:
            total_inv_degree.append(1/degrees[v])
            if bot_labels[v] == 1:
                total_labeled_inv_degree.append(1/degrees[v])
            else:
                total_labeled_inv_degree.append(0)
        else:
            total_inv_degree.append(
                total_inv_degree[i-cut-1] + 1/degrees[v])
            if bot_labels[v] == 1:
                total_labeled_inv_degree.append(
                    total_labeled_inv_degree[i-cut-1] + 1/degrees[v])
            else:
                total_labeled_inv_degree.append(
                    total_labeled_inv_degree[i-cut-1])

        est_0toi.append(
            total_labeled_inv_degree[i-cut]/total_inv_degree[i-cut])

    for e in est_0toi:
        write_to_file(est_file_path, str(e))

    print("Bot population:", est_0toi[-1])


def randomwalk_for_samplesize(api, bom, samplesize, startnode, log_file_path, samplinglist_file_path,
                              calc_bot_ppl=False, threshold=0.95, cut=0, botscore_file_path="", est_file_path=""):
    write_to_file(log_file_path, "Target sample size: %d" % samplesize)
    visit = {}
    friends_dict = {}
    followers_dict = {}
    neighbors_dict = {}

    samplinglist = []
    rw_sequence = []
    degrees = {}
    bot_labels = {}

    v = startnode
    sample_number = 0
    write_to_file(log_file_path, "Started random walk sampling at " +
                  str(datetime.datetime.now()))
    while sample_number < samplesize:
        try:
            next_v = walk(api, v, samplinglist, friends_dict,
                          followers_dict, neighbors_dict, visit, log_file_path, samplinglist_file_path)
            if next_v:
                sample_number += 1
                write_to_file(log_file_path, "Sample %d at %s (%s)" %
                              (sample_number, str(datetime.datetime.now()), v))
                if calc_bot_ppl:
                    rw_sequence.append(v)
                    degrees[v] = samplinglist[-1][3]
                    bot_score = calculate_bot_score(bom, v, botscore_file_path)
                    bot_labels[v] = 1 if bot_score >= threshold else 0
                v = next_v
            else:
                message = "Random walk cannot be performed."
                raise SelectNeighborError(message)
        except GetNeighborsError as e:
            raise e

    write_to_file(log_file_path, "Finished random walk sampling at " +
                  str(datetime.datetime.now()))
    if calc_bot_ppl:
        calculate_bot_population(
            rw_sequence, bot_labels, degrees, cut, est_file_path)


def randomwalk_for_timedelta(api, bom, timedelta, startnode, log_file_path, samplinglist_file_path,
                             calc_bot_ppl=False, threshold=0.95, cut=0, botscore_file_path="", est_file_path=""):
    write_to_file(log_file_path, "Experiment time: %s" % str(timedelta))
    visit = {}
    friends_dict = {}
    followers_dict = {}
    neighbors_dict = {}

    samplinglist = []
    rw_sequence = []
    degrees = {}
    bot_labels = {}

    v = startnode
    sample_number = 0
    limit_date = datetime.datetime.now() + timedelta
    write_to_file(log_file_path, "Started random walk sampling at " +
                  str(datetime.datetime.now()))
    while datetime.datetime.now() < limit_date:
        try:
            next_v = walk(api, v, samplinglist, friends_dict,
                          followers_dict, neighbors_dict, visit, log_file_path, samplinglist_file_path)
            if next_v:
                sample_number += 1
                write_to_file(log_file_path, "Sample %d at %s (%s)" %
                              (sample_number, str(datetime.datetime.now()), v))
                if calc_bot_ppl:
                    rw_sequence.append(v)
                    degrees[v] = samplinglist[-1][3]
                    bot_score = calculate_bot_score(bom, v, botscore_file_path)
                    bot_labels[v] = 1 if bot_score >= threshold else 0
                v = next_v
            else:
                message = "Random walk cannot be performed."
                raise SelectNeighborError(message)
        except GetNeighborsError as e:
            raise e
    write_to_file(log_file_path, "Finished random walk sampling at " +
                  str(datetime.datetime.now()))
    if calc_bot_ppl:
        calculate_bot_population(
            rw_sequence, bot_labels, degrees, cut, est_file_path)


def command_rw(args):
    now = datetime.datetime.now()
    filepath_base = now.strftime("%Y-%m-%d-%H-%M-%S") + \
        "-initial" + str(args.initial_user)
    if args.samplesize:
        filepath_base += "-samplesize" + str(args.samplesize)
    else:
        filepath_base += "-time" + \
            str(args.days) + "d" + str(args.hours) + \
            "h" + str(args.minutes) + "m"

    log_file_path = filepath_dir + filepath_base + "-log" + filepath_ext
    samplinglist_file_path = filepath_dir + \
        filepath_base + "-samplinglist" + filepath_ext
    botscore_file_path = filepath_dir + filepath_base + "-botscore" + filepath_ext
    est_file_path = filepath_dir + filepath_base + "-threshold" + \
        str(args.threshold) + "-cut" + str(args.cut) + "-est" + filepath_ext

    print(filepath_base, "\nResults will be saved to", filepath_dir)

    api_t = get_twitter_api_instance()
    bom = get_botometer_instance()
    if args.samplesize:
        randomwalk_for_samplesize(
            api_t, bom, args.samplesize, args.initial_user, log_file_path, samplinglist_file_path,
            args.calc_bot_ppl, args.threshold, args.cut, botscore_file_path, est_file_path)
    else:
        timedelta = datetime.timedelta(
            days=args.days, hours=args.hours, minutes=args.minutes)
        randomwalk_for_timedelta(
            api_t, bom, timedelta, args.initial_user, log_file_path, samplinglist_file_path,
            args.calc_bot_ppl, args.threshold, args.cut, botscore_file_path, est_file_path)


def command_bot(args):
    file_path = args.file
    file_path = file_path[:-len(filepath_ext)]
    print("Read", file_path)

    if file_path.endswith("-samplinglist"):
        f = open(args.file, 'r')
        lines = f.readlines()
        f.close()

        rw_sequence = []
        degrees = {}
        for line in lines:
            data = line[:-1].split(' ')
            v = int(data[0])
            rw_sequence.append(v)
            degrees[v] = int(data[3])

        file_path = file_path[:-len("-samplinglist")]
        botscore_file_path = file_path + "-botscore" + filepath_ext

        bom = get_botometer_instance()
        bot_labels = {}
        for v in rw_sequence:
            bot_score = calculate_bot_score(bom, v, botscore_file_path)
            bot_labels[v] = 1 if bot_score >= args.threshold else 0
    elif file_path.endswith("-botscore"):
        samplinglist_file = file_path[:-len("botscore")]
        samplinglist_file = samplinglist_file + "samplinglist" + filepath_ext

        f = open(samplinglist_file, 'r')
        lines = f.readlines()
        f.close()
        rw_sequence = []
        degrees = {}
        for line in lines:
            data = line[:-1].split(' ')
            v = int(data[0])
            rw_sequence.append(v)
            degrees[v] = int(data[3])

        f = open(args.file, 'r')
        lines = f.readlines()
        f.close()
        bot_labels = {}
        for line in lines:
            data = line[:-1].split(' ')
            v = int(data[0])
            bot_score = float(data[1])
            bot_labels[v] = 1 if bot_score >= args.threshold else 0

        file_path = file_path[:-len("-botscore")]
    else:
        raise InvalidFilePathError(
            "Please specify valid -samplinglist/-botscore file path.")

    est_file_path = file_path + "-threshold" + str(args.threshold) \
        + "-cut" + str(args.cut) + "-est" + filepath_ext

    calculate_bot_population(rw_sequence, bot_labels,
                             degrees, args.cut, est_file_path)


def main():
    # Arguments
    # Usage: bot_population_estimator.py [-h] {rw,bot} ...
    parser = argparse.ArgumentParser(
        description="Bot Population Estimator via Random Walk")
    subparsers = parser.add_subparsers()

    parser_rw = subparsers.add_parser('rw', help='perform random walk')
    parser_rw.add_argument('-i', '--initial-user', metavar="user_id", type=int,
                           help='initial user id (64-bit integer)', required=True)
    group_random_walk_opt = parser_rw.add_mutually_exclusive_group(
        required=True)
    group_random_walk_opt.add_argument('-r', '--samplesize', metavar="num_samples", type=int,
                                       help='number of samples to collect')
    group_random_walk_opt.add_argument('--days', metavar="num_days", type=int,
                                       help='sampling time [days]', default=0)
    group_random_walk_opt.add_argument('--hours', metavar="num_hours", type=int,
                                       help='sampling time [hours]', default=0)
    group_random_walk_opt.add_argument('--minutes', metavar="num_minutes", type=int,
                                       help='sampling time [minutes]', default=0)
    parser_rw.add_argument('--calc-bot-ppl', action="store_true",
                           help='calculate bot score simultaneously, and the bot population is output at the end.')
    parser_rw.add_argument('-t', '--threshold', metavar="threshold_score", type=float,
                           help="threshold to classify whether a user is bot (default is 0.95)", default=0.95)
    parser_rw.add_argument('-c', '--cut', metavar="num_cut_samples", type=int,
                           help="number of the first samples to be discarded", default=0)
    parser_rw.set_defaults(subcommand_func=command_rw)

    parser_bot = subparsers.add_parser(
        'bot', help='calculate bot score and population with reading samplinglist/botscore file')
    parser_bot.add_argument('-f', '--file', metavar="file_path", type=str,
                            help="path to -samplinglist/-botscore file", required=True)
    parser_bot.add_argument('-t', '--threshold', metavar="threshold_score", type=float,
                            help="threshold to classify whether a user is bot (default is 0.95)", default=0.95)
    parser_bot.add_argument('-c', '--cut', metavar="num_cut_samples", type=int,
                            help="number of the first samples to be discarded", default=0)
    parser_bot.set_defaults(subcommand_func=command_bot)

    args = parser.parse_args()

    if hasattr(args, 'subcommand_func'):
        args.subcommand_func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
