#!/usr/bin/env python3
#
# Copyright 2016 Sarah Sharp <sharp@otter.technology>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
from datetime import datetime, timedelta
import os
from math import sqrt
import json
from ghcategorize import jsonIsPullRequest, jsonIsPullRequestComment, getUserDate
from scipy import stats
import numpy

# When faced with a bunch of data on participation rates of contributors,
# people often want to ask questions about what impacts participation.
# For example, does working with a specific contributor correllate with
# increased participation?
#
# In order to answer these questions, we turn to a particular statistical
# method called hypothesis testing, specifically two-means hypothesis testing.
# Hypothesis testing allows you to answer questions like, "Does working with a
# particular contributor mean a pull request is more likely to be merged?"
#
# However, hypothesis testing does not help you specify *how much* of an impact
# working with that person makes on participation rates. It simply tells you
# that working with that person has a statistically significant impact on
# participation rates. In order to understand the magnitude of the impact the
# person has on contributors, we would instead calculate the effect size, or
# the difference between the mean participate rate of those contributors that
# did and those contributors that did not interact with the contributor (while
# also taking into account the variance, or standard deviation, in the
# participation rates of the whole group).
#
# Resources:
#
# "Probablity and Statistics for Engineers and Scientists", 8th edition by
# Walpole, Myers, Myers, and Ye, Copyright 2007
#
# "It's the Effect Size, Stupid", accessed 11/08/2016
# http://www.leeds.ac.uk/educol/documents/00002182.htm

# In this particular example, we examine the impact of a particular github bot,
# rust-highfive, on whether a pull request is merged or not merged.
#
# The bot, rust-highfive, looks at the files that a contributor changes in
# their pull request, and mentions one reviewer that would be appropriate to
# look at those files. One would hope that by sending a contributor a
# notification for code they should review, that the right people look at pull
# requests, and thus the number of pull requests merged would increase after
# the bot started suggesting reviewers. (It will also be interesting to look at
# length of time the PR was open, but we'll get to that later.)
#
# With two-means hypothesis testing, we first generate a "null hypothesis" that
# represents the "status quo", H0:
#
# H0 = "Interacting with rust-highfive has no impact on whether pull requests
#       are merged."
#
# We generate an "alternative hypothesis", H1, that represents a hypothesis we
# want to test:
#
# H1 = "Interacting with rust-highfive means more pull requests are merged."

# In order to test these two hypothesis, we divide the pull requests into two
# populations: those PRs where rust-highfive commented, and those PRs where it
# did not.
def separatePRs(repoPath, username, startDate, endDate):
    interaction = []
    noInteraction = []
    # Save the pr-*.txt filenames where username commented
    # in the comment or pr-comment
    for directory in os.listdir(repoPath):
        if not os.path.isdir(os.path.join(repoPath, directory)):
            continue

        match = False
        files = os.listdir(os.path.join(repoPath, directory))
        prFile = [x for x in files if jsonIsPullRequest(x)]
        if not prFile:
            continue

        # Figure out whether this pull request was merged or not
        with open(os.path.join(repoPath, directory, prFile[0])) as f:
            prSoup = json.load(f)
        if startDate and datetime.strptime(prSoup['created_at'], "%Y-%m-%dT%H:%M:%SZ") < startDate:
            continue
        if endDate and datetime.strptime(prSoup['created_at'], "%Y-%m-%dT%H:%M:%SZ") > endDate:
            continue

        if not prSoup['merged']:
            merged = 0
            seconds = None
        else:
            merged = 1
            ctime = datetime.strptime(prSoup['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            mtime = datetime.strptime(prSoup['merged_at'], "%Y-%m-%dT%H:%M:%SZ")
            seconds = (mtime - ctime).total_seconds()
            if (seconds < 0):
                print("WARN: PR", os.path.join(repoPath, directory, prFile[0]), "merged before it was created?")
                print("Created", ctime)
                print("Merged", mtime)
                seconds = 0
            else:
                # Convert to hours, to make graphs easier to read
                seconds = seconds / (60.*60)

        # Figure out if username made an issue or pr comment
        comments = [x for x in files if jsonIsPullRequestComment(x) or x.startswith('comment-')]
        for cfile in comments:
            with open(os.path.join(repoPath, directory, cfile)) as commentFile:
                soup = json.load(commentFile)
                user, date = getUserDate(soup)
                if user == username:
                    match = True
        if match:
            interaction.append((os.path.join(repoPath, directory), merged, seconds))
        else:
            noInteraction.append((os.path.join(repoPath, directory), merged, seconds))
    return interaction, noInteraction

def separateByDate(repoPath, cutoff, startDate, endDate):
    older = []
    newer = []
    for directory in os.listdir(repoPath):
        if not os.path.isdir(os.path.join(repoPath, directory)):
            continue

        match = False
        files = os.listdir(os.path.join(repoPath, directory))
        prFile = [x for x in files if jsonIsPullRequest(x)]
        if not prFile:
            continue

        # Figure out whether this pull request was merged or not
        with open(os.path.join(repoPath, directory, prFile[0])) as f:
            prSoup = json.load(f)

        if not prSoup['merged']:
            merged = 0
            seconds = None
        else:
            merged = 1
            ctime = datetime.strptime(prSoup['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            mtime = datetime.strptime(prSoup['merged_at'], "%Y-%m-%dT%H:%M:%SZ")
            seconds = (mtime - ctime).total_seconds()
            if (seconds < 0):
                print("WARN: PR", os.path.join(repoPath, directory, prFile[0]), "merged before it was created?")
                print("Created", ctime)
                print("Merged", mtime)
                seconds = 0
            else:
                # Convert to hours, to make graphs easier to read
                seconds = seconds / (60.*60)
        if (startDate and ctime < startDate) or (endDate and ctime > endDate):
            continue
        if ctime < cutoff:
            older.append((os.path.join(repoPath, directory), merged, seconds))
        else:
            newer.append((os.path.join(repoPath, directory), merged, seconds))
    return older, newer

# Now that we have the dataset for our two populations, we find:
def hypothesisTest(values1, values2, d0, debug):
    #   x1 = mean of the values of population1
    x1 = numpy.mean(values1)
    #   x2 = mean of the values of population2
    x2 = numpy.mean(values2)
    #   d0 = the hyopethical difference between the means of the two populations
    #         we assume must exist if our hypothesis H0 is true.
    #         In this case, we assume there is no difference, so d0 = 0.
    #   s1 = standard deviation of population1
    s1 = numpy.std(values1)
    #   s2 = standard deviation of population2
    s2 = numpy.std(values2)
    #   n1 = number of samples in population1
    n1 = len(values1)
    #   n2 = number of samples in population2
    n2 = len(values2)

    # Our next step is to use a "Two-Sample Pooled T-Test".
    #
    # First, we use those values to calculate the standard deviation across
    # both populations:
    #
    sp = sqrt((s1**2 * (n1 - 1) + s2**2 * (n2 - 1)) /
              (n1 + n2 - 2))

    # We use the standard deviation of the population to calculate the "test
    # value":
    #
    t = (((x1 - x2) - d0) /
         (sp * sqrt(1/n1 + 1/n2)))

    # What does all of this get us? We want to know if the "test value" we
    # calculated is statistically significant. Because we're taking a "random
    # sample" of all possible open source developers (in this case, a sample
    # that participates in one community), some developers will react
    # differently to notifications than others, and the example community's
    # reactions to the bot may change over time. So what is the probably of
    # finding a group of random developers who respond to the bot (and its
    # notifications) positively when the actual response to a bot is less
    # positive?

    # To answer that question, we turn to the Student t-distribution to help
    # us.  The probability distribution curve for a t-distribution is going to
    # look very different depending on the sample size we take. If we take a
    # small sample, the chances of the results of our hypothesis testing being
    # statistically significant is going to be much worse than if we take a
    # larger sample.

    # In this case, we take the area of the probability distribution curve
    # after the value t, and that gives us the statistical significance of our
    # result.  In general scientists don't accept results where the statistical
    # significance, a > 0.05. If you want to get really precise, you only
    # reject H0 if a > 0.01.

    # The area under the t-distribution at point t gives us a, and we reject H1
    # when the area under the probability curve at point t (denoted as P) is less
    # than a = 0.05

    # degrees of freedom is the total number of samples - 2
    # cdf is the probability that X will take a value less than or equal to t
    # however, we want the area under the t-distribution *after* t,
    # so we subtract that probability from 1 to get the area after t.
    p = 1 - stats.t.cdf(t, n1 + n2 - 2)
    if (debug):
        print("Population H0: mean =", x1, "std dev = ", s1, "count =", n1)
        print("Population H1: mean =", x2, "std dev = ", s2, "count =", n2)
        print("std dev =", sp, "t value =", t, "p =", p)
    return t, p, x1, x2

def printTime(days):
    retval = ""
    if days < 1:
        return "{0:.0f}".format(days*24) + " hours"
    if days < 7:
        return "{0:.1f}".format(days) + " days"
    if days < 7*4:
        return "{0:.1f}".format(days / 7) + " weeks"
    return "{0:.1f}".format(hours / (7*4)) + " months"

def testSuccessfulMerges(pop1, pop2, username, quantity, inaction, action, debug):
    print()
    t, p, x1, x2 = hypothesisTest([x[1] for x in pop1],[x[1] for x in pop2], 0, debug)
    if p < 0.01:
        print("We have 99% confidence that", username, "causes", quantity, "pull requests to be merged.")
    elif p < 0.05:
        print("We have 95% confidence that", username, "causes", quantity, "pull requests to be merged.")
    else:
        print(username, "does not cause", quantity, "pull requests to be merged.")

    if p < 0.05:
        print("{0:.1f}%".format(x1*100),
              "of pull requests where", username, action, "were merged.")
        print("{0:.1f}%".format(x2*100),
              "of pull requests where ", username, inaction, "were merged.")
        print("When", username, "recommended a reviewer,",
              "{0:.1f}%".format((x1-x2)*100),
              "more pull requests were merged")

# This function measures whether a user has an impact on the length of time a PR is open.
# H0: Average PR open time without the user (u1) = Average time with the user (u2)
# H1: Average PR open time without the user (u1) > Average time with the user (u2)
# pop1 is the population values without the user
# pop2 is the population values with the user
# inaction is the past-tense string descriptor for the impact of not having the user
# action is the past-tense string descriptor for what the user does
# debug causes the p-value, t-value, means, and standard deviation to be printed
def testPROpenLength(pop1, pop2, username, inaction, action, debug):
    print()
    interactValues = [x[2]/24. for x in pop1 if x[1] == 1]
    noInteractValues = [x[2]/24. for x in pop2 if x[1] == 1]
    t, p, x1, x2 = hypothesisTest(interactValues, noInteractValues, 0, debug)
    if p < 0.01:
        print("We have 99% confidence that pull requests where", username,
              inaction, "remain open for more time.")
    elif p < 0.05:
        print("We have 95% confidence that pull requests where", username,
              inaction, "remain open for more time.")
    else:
        print("No conclusions can be reached with 95% certainty about whether")
        print("pull requests where", username, inaction, "remain open for more time.")

    if p < 0.05:
        print(printTime(x1), "was the average length of time pull requests were open when",
              username, inaction)
        print(printTime(x2), "was the average length of time pull requests were open when",
              username, action)
        print("Merged pull requests where", username, inaction, "were open",
              printTime(x1-x2), "more on average.")

def main():
    parser = argparse.ArgumentParser(description='Gather statistics from scraped github information.')
    parser.add_argument('repository', help='github repository name')
    parser.add_argument('owner', help='github username of repository owner')
    parser.add_argument("--debug", help="Print detailed statistics (sample count, std dev, t-value, and p-values)",
                        action="store_true", default=False)
    args = parser.parse_args()

    print()
    # rust-highfive joined on 2014-09-18T23:32:23Z
    # Let's check only the year of pull requests before rust-highfive
    print("Comparing rust-highfive against pull requests from 2013-09-18 to 2015-09-18:")
    print("============================================================================")
    startDate = datetime.strptime("2013-09-18T23:32:23Z", "%Y-%m-%dT%H:%M:%SZ")
    endDate = datetime.strptime("2015-09-18T23:32:23Z", "%Y-%m-%dT%H:%M:%SZ")
    rhf, norhf = separatePRs(os.path.join(args.owner, args.repository), 'rust-highfive', startDate, endDate)
    testSuccessfulMerges(norhf, rhf, "rust-highfive", "more", "recommended a reviewer", "did not comment", args.debug)
    testPROpenLength(norhf, rhf, "rust-highfive", "did not comment", "recommended a reviewer", args.debug)
    testPROpenLength(rhf, norhf, "rust-highfive", "recommended a reviewer", "did not comment", args.debug)

    # bors first started merging pull requests on 2013-02-02T00:46:02Z
    # Break the data into pull requests before that date and after that date.
    # See if bors had any impact on the percentage of successful merges
    # or length of time a PR remains open.
    # x1 = mean for pop1 (when bors interacted)
    # x2 = mean for pop2 (when bors didn't interact)
    print()
    print("Comparing bors against pull requests from 2012-02-02 to 2014-02-02:")
    print("===================================================================")
    nobors, bors = separateByDate(os.path.join(args.owner, args.repository),
                                datetime.strptime("2013-02-02T00:46:02Z", "%Y-%m-%dT%H:%M:%SZ"),
                                datetime.strptime("2012-02-02T00:46:02Z", "%Y-%m-%dT%H:%M:%SZ"),
                                datetime.strptime("2014-02-02T00:46:02Z", "%Y-%m-%dT%H:%M:%SZ"))
    testSuccessfulMerges(nobors, bors, "bors", "more", "was not used", "initiated a CI test", args.debug)
    #testSuccessfulMerges(bors, nobors, "bors", "less", "initiated a CI test", "was not used", args.debug)
    testPROpenLength(nobors, bors, "bors", "was not used", "initiated a CI test", args.debug)
    testPROpenLength(bors, nobors, "bors", "initiated a CI test", "was not used", args.debug)

if __name__ == "__main__":
    main()
