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
-------------------------

If you are new to git and unfamiliar with many of the terminologies, `Dangit, Git?! <https://dangitgit.com/>`__ provides solutions *in plain English* to many common mistakes people have made.

There are many comprehensive online git tutorials, such as:

- The official `git tutorial <https://git-scm.com/docs/gittutorial>`__.
- A more verbose `introduction <https://www.atlassian.com/git/tutorials/what-is-version-control>`__ to the ideas behind git and version control.
- A still more detailed `walkthrough <http://swcarpentry.github.io/git-novice/>`__, assuming no prior knowledge.

Set up SSH with GitHub
----------------------

- You have to generate an `SSH key <https://help.github.com/en/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent>`__ and `add it <https://help.github.com/en/articles/adding-a-new-ssh-key-to-your-github-account>`__ to your GitHub account. This will save you from having to re-enter your GitHub username and password every time you interact with their servers.
- When generating the SSH key, you'll be asked to pick a *passphrase* (i.e., password).
- The following instructions assume you've generated an SSH key. If you're using manual authentication instead, replace the "``git@github.com:``" addresses in what follows with "``https://github.com/``".

Clone a local repository onto your machine
------------------------------------------

- *Clone* your fork onto your computer: ``git clone git@github.com:<your_github_account>/MDTF-diagnostics.git``. This not only downloads the files, but due to the magic of git  also gives you the full commit history of all branches.
- Enter the project directory: ``cd MDTF-diagnostics``.
- Clone additional dependencies of the code: ``git submodule update --recursive --init``.
- Git knows about your fork, but you need to tell it about NOAA's repo if you wish to contribute changes back to the code base. To do this, type ``git remote add upstream git@github.com:NOAA-GFDL/MDTF-diagnostics.git``. Now you have two remote repos: ``origin``, your GitHub fork which you can read and write to, and ``upstream``, NOAA's code base which you can only read from.

.. (TODO: `pip install -v .`, other installation instructions...)

Start coding
------------

1. Switch to the ``develop`` branch
::
  git checkout develop

2. Make sure that you pull in changes from the develop branch frequently to simplify the merge process after you submit a PR. Update your local copy (the copy on your computer) of the develop branch
::
  git fetch upstream develop
  git pull upstream develop
  git submodule update --recursive --remote

3. Next, update your remote copy (the branch on your Github fork)
::
  git push origin develop

4. Now your branch is up-to-date, and you are ready to start working on a new feature
::
  git checkout -b feature/<my_feature_name>

will create a new branch (``-b`` flag) off of ``develop`` and switch you to working on that branch.

Updating your feature branch by merging in changes from the develop branch
---------------------------------------------------------------------------
1. Update the local and remote develop branches on your fork as described steps 1--3  of the **Start Coding** section, check out your feature branch, and merge the develop branch into your feature branch
::
  git checkout feature/<my_feature_name>
  git merge develop

2. Resolve any conflicts that occur from the merge

3. Add the updated files to the staging area
::
  git add file1
  git add file2
  ...

4. Push the branch updates to your remote fork
::
  git push origin feature/<my_feature_name>

Reverting commits
^^^^^^^^^^^^^^^^^
If you want to revert to the commit(s) before you pulled in updates:

1. Find the commit hash(es) with the updates, in your git log
::
  git log

or consult the commit log in the web interface

2. Revert each commit in order from newest to oldest
::
  git revert <newer commit hash>
  git revert <older commit hash>

3. Push the updates to the remote branch
::
  git push origin feature/<my_feature_name> --force

Updating a branch with a 2-step merge 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you are concerned with updates breaking your development branch, but don't want to deal with undoing commits, you can test the updates in a copy of your feature branch, then merge the copy branch into your feature branch:

1. Check out your feature branch
::
  git checkout feature/<my_feature_name>

2. Check out a new branch from the feature branch
::
  git checkout -b <test_branch_name>

3. Merge develop into the test branch using the procedure described in the previous section

4. Test the branch with the MDTF framework software

5. Check out your feature branch, then merge the test branch into the feature branch
::
  git checkout feature/<my_feature_name>
  git merge <test_branch_name>

6. Push the updates to your remote branch
::
  git push origin feature/<my_feature_name>

7. Delete the test branch
::
  git branch -D <test_branch_name>

Updating your feature branch by rebasing it onto the develop branch (preferred method)
--------------------------------------------------------------------------------------
Rebasing is procedure to integrate the changes from one branch into another branch. ``git rebase`` differs from ``git merge`` in that it reorders the commit history so that commits from the branch that is being updated are moved to the `tip` of the branch. This makes it easier to isolate changes in the feature branch, and usually results in fewer merge conflicts when the feature branch is merged into the develop branch.

1. Update the local and remote develop branches on your fork as described steps 1--3  
of the **Start Coding** section, then check out your feature branch
::
  git checkout feature/<my_feature_name>

and launch an interactive rebase of your branch onto the develop branch.
::
  git rebase -i develop
2. Your text editor will open in the terminal (Vim by default)
and display your commit hashes with the oldest commit at the top
::
  pick 39n3b42 oldest commit
  pick 320cnyn older commit
  pick 20ac93c newest commit

You may squash commits by replacing *pick* with *squash* for the commit(s) that are newer than the commit you want to combine with (i.e., the commits below the target commit).
For example
::
  pick 39n3b42 oldest commit
  squash 320cnyn older commit
  pick 20ac93c newest commit
combines commit 320cnyn with commit 29n3b42, while
::
  pick 39n3b42 oldest commit
  squash 320cnyn older commit
  squash 20ac93c newest commit
combines 20ac93c and 320cnyn with 39n3b42.

Note that squashing commits is not required. However, doing so creates a more streamlined commit history.

3. Once you're done squashing commits (if you chose to do so), save your changes and close the editor ``ESC + SHIFT + wq`` to save and quit in Vim), and the rebase will launch. If the rebase stops because there are merge conficts and resolve the conflicts. To show the files with merge conflicts, type
::
git status

This will show files with a message that there are merge conflicts, or that a file has been added/deleted by only one of the branches. Open the files in an editor, resolve the conflicts, then add edited (or remove deleted) files to the staging area
::
  git add file1
  git add file2
  ...
  git rm file3
4. Next, continue the rebase
::
  git rebase --continue

The editor will open with the modified commit history. Simply save the changes and close the editor (``ESC+SHIFT+wq``), and the rebase will continue. If the rebase stops with errors, repeat the merge conflict resolution process, add/remove the files to staging area, type ``git rebase --continue``, and proceed.

If you have not updated your branch in a long time, you'll likely find that you have to keep fixing the same conflicts over and over again (every time your commits collide with the commits on the main branch). This is why we strongly advise POD developers to pull updates into their forksand rebase their branches onto the develop branch frequently.

Note that if you want to stop the rebase at any time and revert to the original state of your branch, type
::
  git rebase --abort

5. Once the rebase has completed, push your changes to the remote copy of your branch
::
  git push origin feature/<my_feature_name> --force
The ``--force`` option is necessary because rebasing modified the commit history.

6. Now that your branch is up-to-date, write your code!

Pushing to your remote POD development branch on your fork
----------------------------------------------------------
When you are ready to push your updates to the remote branch on your fork

1. type ``git status`` to list the file(s) that have been updated

2. type ``git add <file>`` to add individual files, or ``git add --all`` to add all files, that have been updated to the staging area

3. Commit the changes with ``git commit -m <your commit message>``. You can also type ``git commit`` to launch an editor in the terminal where you can enter your message.

If you use the editor or BASH shell, you can easily break up your message over multiple lines for better readability.

4. Push the updates to your fork: ``git push -u origin feature/<my_feature_name>`` (The ``-u`` flag is for creating a new branch remotely and only needs to be used the first time.)

Pull Requests
-------------
A Pull Request (PR) is your proposal to the maintainers to incorporate your feature into NOAA's repo. When your feature is ready, submit a PR by going to the GitHub page of your fork and clicking on **Pull request** to the right of the branch description. Make sure you are submitting the PR to NOAA-GFDL/develop. Enter a brief description for the PR, and check the boxes in the to-do list for the completed tasks. If you are still working on your POD, but want to test it with the CI, you can select the *Create Draft Pull Request* option from the dropdown menu by clicking the green button with the arrow to the right of the **Create Pull Request Button**.

Git Tips and Tricks
-------------------
* If you are unfamiliar with git and want to practice with the commands listed here, we recommend you to create an additional feature branch just for this. Remember: your changes will not affect NOAA's repo until you've submitted a pull request through the GitHub webpage and accepted by the lead-team programmer.

* GUI applications can be helpful when trying to resolve merge conflicts.Git packages for IDEs such as VSCode and Eclipse often include tools for merge conflict resolution. You can also install free versions of merge-conflict tools like `P4merge <https://www.perforce.com/products/helix-core-apps/merge-diff-tool-p4merge>`__ and `Sublime merge <https://www.sublimemerge.com/>`__.

* If you encounter problems during practice, you can first try looking for *plain English* instructions to fix the situation at `Dangit, Git?! <https://dangitgit.com/>`__.

* A useful command is ``git status`` to remind you what branch you're on and changes you've made (but have not committed yet).

* ``git branch -a`` lists all branches with ``*`` indicating the branch you're on.
     
* Push your changes to your remote fork often (at least daily) even if your changes aren't "clean", or you are in the middle of a task. Your commit history does not need to look like a polished document, and nobody is judging your coding prowess by your development branch. Frequently pushing to your remote branch ensures that you have an easily accessible recent snapshot of your code in the event that your system goes down, or you go crazy with ``rm -f *``.

* A commit creates a snapshot of the code into the history in your local repo.
   - The snapshot will exist until you intentionally delete it (after confirming a warning message). You can always revert to a previous snapshot.
   - Don't commit code that you know is buggy or non-functional!
   - You'll be asked to enter a commit message. Good commit messages are key to making the project's history useful.
   - Write in *present tense* describing what the commit, when applied, does to the code -- not what you did to the code.
   - Messages should start with a brief, one-line summary, less than 80 characters. If this is too short, you may want to consider entering your changes as multiple commits.

* Good commit messages are key to making the project's history useful. To make this easier, instead of using the ``-m`` flag, To provide further information, add a blank line after the summary and wrap text to 72 columns if your editor supports it (this makes things display nicer on some tools). Here's an `example <https://github.com/NOAA-GFDL/MDTF-diagnostics/commit/225b29f30872b60621a5f1c55a9f75bbcf192e0b>`__.

* To configure git to launch your text editor of choice: ``git config --global core.editor "<command string to launch your editor>"``.

* To set your email: ``git config --global user.email "myemail@somedomain.com"`` You can use the masked email github provides if you don't want your work email included in the commit log message. The masked email address is located in the `Primary email address` section under Settings>emails. 

* When the feature branch is no longer needed, delete the branch locally with ``git branch -d feature/<my_feature_name>``.
 If you pushed the feature branch to your fork, you can delete it remotely with ``git push --delete origin feature/<my_feature_name>``.
   * Remember that branches in git are just pointers to a particular commit, so by deleting a branch you *don't* lose any history.

* If you want to let others work on your feature, push its branch to your GitHub fork with ``git push -u origin feature/<my_feature_name>``.

* For additional ways to undo changes in your branch, see `How to undo (almost) anything with Git <https://github.blog/2015-06-08-how-to-undo-almost-anything-with-git/>`__.


.. (TODO: tests ...)
.. (... policy on CI, tests passing ...)
