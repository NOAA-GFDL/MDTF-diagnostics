.. _ref-dev-git-intro:

Git-based development workflow
==============================

We recommend developers to manage the MDTF package using the GitHub webpage interface:

- If you have no prior experience with `GitHub <https://github.com/>`__, create an account first.

- Create a *fork* of the project by clicking the ``Fork`` button in the upper-right corner of `NOAA's MDTF GitHub page <https://github.com/NOAA-GFDL/MDTF-diagnostics>`__. This will create a copy (also known as *repository*, or simply *repo*) in your own GitHub account which you have full control over.

- Before you start working on the code, remember to switch to the ``develop`` branch (instead of ``main``) as expected from a POD developer.

It should be easy to figure out how to add/edit files through your repo webpage interface.

- After updating the code in your repo, submit a ``Pull request`` so that the changes you have made can be incorporated into the official NOAA's repo.

- Your changes will not affect the official NOAA's repo until the pull request is accepted by the lead-team programmer.

Note that if any buttons are missing, try ``CRTL`` + ``+`` or ``CRTL`` + ``-`` to adjust the webpage font size so the missing buttons may magically appear.

Managing through the webpage interface as described above is quick and easy. Another approach, unfortunately with a steeper learning curve, is to create a local repo on your machine and manage the code using the ``git`` command in a terminal. In the interests of making things self-contained, the rest of this section gives brief step-by-step instructions on git for interested developers.

Before following the instructions below, make sure that a) you've created a fork of the project, and b) the ``git`` command is available on your machine (`installation instructions <https://git-scm.com/download/>`__).

Some online git resources
^^^^^^^^^^^^^^^^^^^^^^^^^

If you are new to git and unfamiliar with many of the terminologies, `Dangit, Git?! <https://dangitgit.com/>`__ provides solutions *in plain English* to many common mistakes people have made.

There are many comprehensive online git tutorials, such as:

- The official `git tutorial <https://git-scm.com/docs/gittutorial>`__.
- A more verbose `introduction <https://www.atlassian.com/git/tutorials/what-is-version-control>`__ to the ideas behind git and version control.
- A still more detailed `walkthrough <http://swcarpentry.github.io/git-novice/>`__, assuming no prior knowledge.

Set up SSH with GitHub
^^^^^^^^^^^^^^^^^^^^^^

- You have to generate an `SSH key <https://help.github.com/en/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent>`__ and `add it <https://help.github.com/en/articles/adding-a-new-ssh-key-to-your-github-account>`__ to your GitHub account. This will save you from having to re-enter your GitHub username and password every time you interact with their servers.
- When generating the SSH key, you'll be asked to pick a *passphrase* (i.e., password).
- The following instructions assume you've generated an SSH key. If you're using manual authentication instead, replace the "``git@github.com:``" addresses in what follows with "``https://github.com/``".

Clone a local repository onto your machine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- *Clone* your fork onto your computer: ``git clone git@github.com:<your_github_account>/MDTF-diagnostics.git``. This not only downloads the files, but due to the magic of git  also gives you the full commit history of all branches.
- Enter the project directory: ``cd MDTF-diagnostics``.
- Clone additional dependencies of the code: ``git submodule update --recursive --init``.
- Git knows about your fork, but you need to tell it about NOAA's repo if you wish to contribute changes back to the code base. To do this, type ``git remote add upstream git@github.com:NOAA-GFDL/MDTF-diagnostics.git``. Now you have two remote repos: ``origin``, your GitHub fork which you can read and write to, and ``upstream``, NOAA's code base which you can only read from.

.. (TODO: `pip install -v .`, other installation instructions...)

Start coding
^^^^^^^^^^^^

- Switch to the ``develop`` branch: ``git checkout develop``.
- If it's been a while since you created your fork, other people may have updated NOAA's ``develop`` branch. To make sure you're up-to-date, get these changes with ``git pull upstream develop`` and ``git submodule update --recursive --remote``.
- That command updates the working copy on your computer, but you also need to tell your fork on GitHub about the changes: ``git push origin develop``.
- Now you're up-to-date and ready to start working on a new feature. ``git checkout -b feature/<my_feature_name>`` will create a new branch (``-b`` flag) off of ``develop`` and switch you to working on that branch.

   - If you are unfamiliar with git and want to practice with the commands listed here, we recommend you to create an additional feature branch just for this. Remember: your changes will not affect NOAA's repo until you've submitted a pull request through the GitHub webpage and accepted by the lead-team programmer.

   - If you encounter problems during practice, you can first try looking for *plain English* instructions to unmess the situation at `Dangit, Git?! <https://dangitgit.com/>`__.

- Write your code! A useful command is ``git status`` to remind you what branch you're on and changes you've made (but have not committed yet). ``git branch -a`` lists all branches with ``*`` indicating the branch you're on.

.. (TODO: tests ...)
.. (TODO: adding files...)
.. (- Commit changes with ``git commit -m <your commit message>``.) Somehow -m never works for YH.
.. Good commit messages are key to making the project's history useful. To make this easier, instead of using the ``-m`` flag, you can configure git to launch your text editor of choice with ``git config --global core.editor "<command string to launch your editor>"``.
.. - To provide further information, add a blank line after the summary and wrap text to 72 columns if your editor supports it (this makes things display nicer on some tools). Here's an `example <https://github.com/NOAA-GFDL/MDTF-diagnostics/commit/225b29f30872b60621a5f1c55a9f75bbcf192e0b>`__.

- If you've added new files, ``git add --all`` before commit the changes.

- Commit changes with ``git commit -a``. This creates a snapshot of the code into the history in your local repo.

   - The snapshot will exist until you intentionally delete it (after confirming a warning message). You can always revert to a previous snapshot.
   - Don't commit code that you know is buggy or non-functional!
   - You'll be asked to enter a commit message. Good commit messages are key to making the project's history useful.
   - Write in *present tense* describing what the commit, when applied, does to the code -- not what you did to the code.
   - Messages should start with a brief, one-line summary, less than 80 characters. If this is too short, you may want to consider entering your changes as multiple commits.

- When finish updating your feature, merge it back into ``develop``: first ``git checkout develop`` then ``git merge --no-ff feature/<my_feature_name>``. **The '--no-ff' flag is important:** it tells git not to compress ("fast-forward") your commit history onto the ``develop`` branch.
- ``git push origin`` so that the changes to your local repo is incorporated to the your GitHub fork (displayed on the webpage).

   - Enter the SSH key *passphrase* when asked for *password*.

- If you haven't finished working on your feature, you can checkout and update the local feature branch again by repeating the above commands.
- When your feature is ready, submit a *pull request* by going to the GitHub page of your fork and clicking on the ``Pull request`` button. This is your proposal to the maintainers to incorporate your feature into NOAA's repo.
- When the feature branch is no longer needed, delete the branch locally with ``git branch -d feature/<my_feature_name>``. If you pushed it to your fork, you can delete it remotely with ``git push --delete origin feature/<my_feature_name>``.

   - Remember that branches in git are just pointers to a particular commit, so by deleting a branch you *don't* lose any history.

- If you want to let others work on your feature, push its branch to your GitHub fork with ``git push -u origin feature/<my_feature_name>``. The ``-u`` flag is for creating a new branch remotely and only needs to be used the first time.

.. (... policy on CI, tests passing ...)
