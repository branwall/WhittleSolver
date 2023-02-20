# Whittle Solver

This script solves the excellent game of [Whittle](https://whittlegame.com) by brute force.

Using `whittle_multithread.py`, users can input a grid of playable squares as Xs and Os, followed by allowable letters, and every permutation of valid words that fit into the grid will be checked for
use of valid letters and appropriate alignment.

Can run through words in the "reduced" wordlists pretty effectively, but might require the `--full` option to use the greater wordlist on days with obscure words in the answer. In this case, good luck: there are often too many permutations to compute in a reasonable amount of time or memory. Anything over ~7 billion easily overflows 128GB of RAM, so you might be better off solving by hand!

After solving, this runs the valid solutions through a dictionary to score them in two ways:

1. Likelihood of being the theme answer. This checks dictionary definitions of each word and looks for words in common.
2. Scrabble score. (Following the same rules as Whittle\*)

\* = Not quite. Whittle removes points from non-overlapping letters in words of length 2. I don't (yet).
