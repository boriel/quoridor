# QUORIDOR

By Jose Rodriguez (a.k.a. Boriel)

This program implements a classic AI (no _deep learning_) [Quoridor](https://en.wikipedia.org/wiki/Quoridor) player using a
[minimax algorithm](https://en.wikipedia.org/wiki/Minimax) with [Alpha-Beta](https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning) pruning.

The heuristic function used is the actual minimum distance from the player pawn to the goal.

## Requirements

This program was first implemented in python 2.6, and now ported to python 3.x. There's no testing (TDD, Unit testing),
so some bugs might have been introduced. I've tested (QA) the ported program playing against it and seems to behave
fairy well.

 * Python 3.x
 * Pygame==1.9.6
 
## Installation

No installation needed. Just run the script with `python quoridor.py`

## Usage

Just run it with `python quoridor.py -l LEVEL`. Level parameter is optional, ans must is a number (defaults to 0 if no
specified). The higher the harder (deeper ahead analysis), but more time and memory required.

## TO DO

Many improvements pending:

 * The program was intended to be decoupled (UI separated from the rest). Indeed there's (now lost) version which used
XMLRPC to play remotely using HTTP. This will allow to AIs to play separately, or two players, or relocate the AI player
in a server.

 * Many refacts pending (i.e. decouple the UI from the rest)
 
 * Modernize the python code.
 
 * Improve code quality.
 
 * Testing
 
 * There's a bug for higher levels still not fixed. The program might play worse (?) or even crash.

## License

[GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)
