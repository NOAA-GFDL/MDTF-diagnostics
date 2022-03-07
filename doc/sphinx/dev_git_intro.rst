Git-based development workflow
==============================

Steps for brand new users:
------------------------------
1. Fork the MDTF-diagnostics branch to your GitHub account (:ref:`ref-fork-code`)
2. Clone (:ref:`ref-clone`) your fork of the MDTF-diagnostics repository (repo) to your local machine (if you are not using the web interface for development)
3. Check out a new branch from the local develop branch (:ref:`ref-new-feature`)
4. Start coding
5. Commit the changes in your feature branch (:ref:`ref-new-feature`)
6. Push the changes to the copy of the feature branch on your remote fork (:ref:`ref-new-feature`)
7. Repeat steps 4--6 until you are finished working
8. Submit a pull request to the NOAA-GFDL repo for review (:ref:`ref-pull-request`).

Steps for users continuing work on an existing feature branch
-------------------------------------------------------------
1. Create a backup copy of the MDTF-Diagnostics repo on your local machine
2. Pull in updates from the NOAA-GFDL/develop branch to the develop branch in your remote repo (:ref:`ref-update-develop`)
3. Pull in updates from develop branch in your remote fork into the develop branch in your local repo (:ref:`ref-update-develop`)
4. Sync your feature branch in your local repository with the local develop branch using an interactive rebase (:ref:`ref-rebase`) or merge (:ref:`ref-merge`). Be sure to make a backup copy of of your local *MDTF-diagnostics* repo first, and test your branch after rebasing/merging as described in the linked instructions before proceeding to the next step.
5. Continue working on your feature branch
6. Commit the changes in your feature branch
7. Push the changes to the copy of the feature branch in your remote fork (:ref:`ref-push`)
8. Submit a pull request (PR) to NOAA-GFDL/develop branch when your code is ready for review (:ref:`ref-pull-request`)

.. _ref-fork-code:

Creating a fork of the MDTF-diagnostics repository
--------------------------------------------------
- If you have no prior experience with `GitHub <https://github.com/>`__, create an account first.

- Create a *fork* of the project by clicking the ``Fork`` button in the upper-right corner of `NOAA's MDTF GitHub page <https://github.com/NOAA-GFDL/MDTF-diagnostics>`__. This will create a copy (also known as *repository*, or simply *repo*) in your own GitHub account which you have full control over.

.. _ref-clone:

Cloning a repository onto your machine
------------------------------------------
Before following the instructions below, make sure that a) you've created a fork of the project, and b) the ``git`` command is available on your machine (`installation instructions <https://git-scm.com/download/>`__).

- *Clone* your fork onto your computer: ``git clone git@github.com:<your_github_account>/MDTF-diagnostics.git``. This not only downloads the files, but due to the magic of git  also gives you the full commit history of all branches.
- Enter the project directory: ``cd MDTF-diagnostics``.
- Git knows about your fork, but you need to tell it about NOAA's repo if you wish to contribute changes back to the code base. To do this, type ``git remote add upstream git@github.com:NOAA-GFDL/MDTF-diagnostics.git``. Now you have two remote repos: ``origin``, your GitHub fork which you can read and write to, and ``upstream``, NOAA's code base which you can only read from.

Another approach is to create a local repo on your machine and manage the code using the ``git`` command in a terminal. In the interests of making things self-contained, the rest of this section gives brief step-by-step instructions on git for interested developers.

.. _ref-new-feature:

Working on a brand new feature
------------------------------
Developers can either clone the MDTF-diagnostics repo to their computer, or manage the MDTF package using the GitHub webpage interface.
Whichever method you choose, remember to create your feature/[POD name] branch from the develop branch, not the main branch.
Since developers commonly work on their own machines, this manual provides command line instructions.

1. Check out a branch for your POD from the develop branch
::

   git checkout -b feature/[POD name] develop

2. Write code, add files, etc...

3. Add the files you created and/or modified to the staging area
::

   git add [file 1]
   git add [file 2]
   ...

4. Commit your changes, including a brief description
::

   git commit -m "description of my changes"

5. Push the updates to your remote repository
::

   git push -u origin feature/[POD name]

.. _ref-push:

Pushing to your remote feature branch on your fork
----------------------------------------------------------
When you are ready to push your updates to the remote feature branch on your fork

1. Type ``git status`` to list the file(s) that have been updated

2. Repeat steps 3--5 of section  (:ref:`ref-new-feature`)

.. _ref-pull-request:

Submitting Pull Requests
------------------------
The pull request (PR) for your branch is your proposal to the maintainers to incorporate your feature into NOAA's repo.
Your changes will not affect the official NOAA's repo until the PR is accepted by the lead-team programmer.
Note that if any buttons are missing, try ``CRTL`` + ``+`` or ``CRTL`` + ``-`` to adjust the webpage font size so the missing buttons may magically appear.

To submit a PR :

1. Click the *Contribute* link on the main page of your MDTF-diagnostics fork and click the *Open Pull Request* button

2. Verify that your fork is set as the **base** repository, and *develop* is set as the **base branch**,
that *NOAA-GFDL* is set as the **head repository**, and *develop* is set as the **head** branch

3. Click the *Create Pull Request* button, add a brief description to the PR header, and go through the checklist to
ensure that your code meets that baseline requirements for review

4. Click the *Create Pull Request* button (now in the lower left corner of the message box).

Note that you can submit a Draft Pull Request if you want to run the code through the CI, but are not ready
for a full review by the framework team. Starting from step 3. above

1. Click the arrow on the right edge of the *Create Pull Request* button and select *Create draft pull request* from the dropdown menu.

2. Continue pushing changes to your feature branch until you are ready for a review (the PR will update automatically)

3. When you are ready for review, navigate to the NOAA-GFDL/MDTF-Diagnostics `*Pull requests* <https://github.com/NOAA-GFDL/MDTF-diagnostics/pulls>`__ page,
and click on your PR

4. Scroll down to the header that states "this pull request is still a work in progress", and click the *ready for review* button to move the PR out of *draft* mode

.. _ref-update-develop:

Updating your remote and local develop branches
-----------------------------------------------

Method 1: Web interface+command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
See the `MDTF Best Practices Overview <https://docs.google.com/presentation/d/18jbi50vC9X89vFbL0W1Ska1dKuW_yWY51SomWx_ahYE/edit?usp=sharing>`__  presentation for instructions with figures.

1. Click the *Fetch Upstream* link on the main page of your MDTF-diagnostics fork, then click the *Open Pull Request* button
2. Verify that your fork is set as the **base** repository, and *develop* is set as the **base branch**,
   that *NOAA-GFDL* is set as the **head repository**, and *develop* is set as the **head** branch
3. Create a title for your PR, add a description if you want, then click *Create pull request*
4. Click **Merge pull request**

Your remote develop branch is now up-to-date with the NOAA-GFDL/develop branch.

5. On your machine, open a terminal and check out the develop branch
::

   git checkout develop

6. Fetch the updates to the develop branch from your remote fork
::

   git fetch

7. Pull in the updates from the remote develop branch.
::

   git pull

Your local develop branch is now up-to-date with the NOAA-GFDL/develop branch.

Method 2: Command line only
^^^^^^^^^^^^^^^^^^^^^^^^^^^
This method requires adding the *NOAA-GFDL/MDTF-diagnostics* repo to the *.git/config* file in your local repo, and is described in the GitHub discussion post `Working with multiple remote repositories in your git config file <https://github.com/NOAA-GFDL/MDTF-diagnostics/discussions/96>`__.


.. (TODO: `pip install -v .`, other installation instructions...)

.. _ref-rebase:

Updating your feature branch by rebasing it onto the develop branch (preferred method)
--------------------------------------------------------------------------------------
Rebasing is procedure to integrate the changes from one branch into another branch. ``git rebase`` differs from ``git merge`` in that it reorders the commit history so that commits from the branch that is being updated are moved to the `tip` of the branch. This makes it easier to isolate changes in the feature branch, and usually results in fewer merge conflicts when the feature branch is merged into the develop branch.
1. Create a backup copy of your MDTF-diagnostics repo on your local machine

2. Update the local and remote develop branches on your fork as described in :ref:`ref-update-develop`, then check out your feature branch
::

   git checkout feature/[POD name]

and launch an interactive rebase of your branch onto the develop branch:: git rebase -i develop
3. Your text editor will open in the terminal (Vim by default)
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

4. Once you're done squashing commits (if you chose to do so), save your changes and close the editor ``ESC + SHIFT + wq`` to save and quit in Vim), and the rebase will launch. If the rebase stops because there are merge conflicts and resolve the conflicts. To show the files with merge conflicts, type
::

   git status

This will show files with a message that there are merge conflicts, or that a file has been added/deleted by only one of the branches. Open the files in an editor, resolve the conflicts, then add edited (or remove deleted) files to the staging area
::

   git add file1
   git add file2
   ...
   git rm file3

5. Next, continue the rebase
::

   git rebase --continue

The editor will open with the modified commit history. Simply save the changes and close the editor (``ESC+SHIFT+wq``), and the rebase will continue. If the rebase stops with errors, repeat the merge conflict resolution process, add/remove the files to staging area, type ``git rebase --continue``, and proceed.

If you have not updated your branch in a long time, you'll likely find that you have to keep fixing the same conflicts over and over again (every time your commits collide with the commits on the main branch). This is why we strongly advise POD developers to pull updates into their forks and rebase their branches onto the develop branch frequently.

Note that if you want to stop the rebase at any time and revert to the original state of your branch, type
::

   git rebase --abort

6. Once the rebase has completed, push your changes to the remote copy of your branch
::

   git push -u origin feature/[POD name] --force

The ``--force`` option is necessary because rebasing modified the commit history.

7. Now that your branch is up-to-date, write your code!

.. _ref-merge:

Updating your feature branch by merging in changes from the develop branch
---------------------------------------------------------------------------
1. Create a backup copy of your repo on your machine.

2. Update the local and remote develop branches on your fork as described in :ref:`ref-update-develop`.

3. Check out your feature branch, and merge the develop branch into your feature branch
::

   git checkout feature/[POD name]
   git merge develop

4. Resolve any conflicts that occur from the merge

5. Add the updated files to the staging area
::

   git add file1
   git add file2
   ...

6. Push the branch updates to your remote fork
::

   git push -u origin feature/[POD name]

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

   git push origin feature/[POD name]

Set up SSH with GitHub
----------------------

- You have to generate an `SSH key <https://help.github.com/en/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent>`__ and `add it <https://help.github.com/en/articles/adding-a-new-ssh-key-to-your-github-account>`__ to your GitHub account. This will save you from having to re-enter your GitHub username and password every time you interact with their servers.
- When generating the SSH key, you'll be asked to pick a *passphrase* (i.e., password).
- The following instructions assume you've generated an SSH key. If you're using manual authentication instead, replace the "``git@github.com:``" addresses in what follows with "``https://github.com/``".


Some online git resources
-------------------------

If you are new to git and unfamiliar with many of the terminologies, `Dangit, Git?! <https://dangitgit.com/>`__ provides solutions *in plain English* to many common mistakes people have made.

There are many comprehensive online git tutorials, such as:

- The official `git tutorial <https://git-scm.com/docs/gittutorial>`__.
- A more verbose `introduction <https://www.atlassian.com/git/tutorials/what-is-version-control>`__ to the ideas behind git and version control.
- A still more detailed `walkthrough <http://swcarpentry.github.io/git-novice/>`__, assuming no prior knowledge.

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
   - Remember that branches in git are just pointers to a particular commit, so by deleting a branch you *don't* lose any history.

* If you want to let others work on your feature, push its branch to your GitHub fork with ``git push -u origin feature/<my_feature_name>``.

* For additional ways to undo changes in your branch, see `How to undo (almost) anything with Git <https://github.blog/2015-06-08-how-to-undo-almost-anything-with-git/>`__.


.. (TODO: tests ...)
.. (... policy on CI, tests passing ...)
