.. _ref-git-intro:
Git-based development workflow
==============================
Steps for brand new users:
--------------------------
#. Fork the MDTF-diagnostics branch to your GitHub account (:ref:`ref-fork-code`)
#. Clone (:ref:`ref-clone`) your fork of the MDTF-diagnostics repository (repo) to your local machine
   (if you are not using the web interface for development)
#. Check out a new branch from the local main branch (:ref:`ref-new-pod`)
#. Start coding
#. Commit the changes in your POD branch (:ref:`ref-new-pod`)
#. Push the changes to the copy of the POD branch on your remote fork (:ref:`ref-new-pod`)
#. Repeat steps 4--6 until you are finished working
#. Submit a pull request to the NOAA-GFDL repo for review (:ref:`ref-pull-request`).

Steps for users continuing work on an existing POD branch
---------------------------------------------------------
#. Create a backup copy of the MDTF-Diagnostics repo on your local machine
#. Pull in updates from the NOAA-GFDL/main branch to the main branch in your remote repo (:ref:`ref-update-main`)
#. Pull in updates from the main branch in your remote fork into the main branch in your local repo
   (:ref:`ref-update-main`)
#. Sync your POD branch in your local repository with the local main branch using an interactive rebase
   (:ref:`ref-rebase`) or merge (:ref:`ref-merge`). Be sure to make a backup copy of of your local *MDTF-diagnostics*
   repo first, and test your branch after rebasing/merging as described in the linked instructions before proceeding
   to the next step.
#. Continue working on your POD branch
#. Commit the changes in your POD branch
#. Push the changes to the copy of the POD branch in your remote fork (:ref:`ref-push`)
#. Submit a pull request (PR) to NOAA-GFDL/main branch when your code is ready for review (:ref:`ref-pull-request`)

.. _ref-fork-code:

Creating a fork of the MDTF-diagnostics repository
--------------------------------------------------
- If you have no prior experience with `GitHub <https://github.com/>`__, create an account first.

- Enable `multifactor authentication <https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/accessing-github-using-two-factor-authentication>`__
  on your Github account

- Create a *fork* of the project by clicking the ``Fork`` button in the upper-right corner of
  `NOAA's MDTF GitHub page <https://github.com/NOAA-GFDL/MDTF-diagnostics>`__.
  This will create a copy (also known as *repository*, or simply *repo*) in your own GitHub account which you have
  full control over.

.. _ref-clone:

Cloning a repository onto your machine
--------------------------------------
Before following the instructions below, make sure that a) you've created a fork of the project, and b) the ``git``
command is available on your machine (`installation instructions <https://git-scm.com/download/>`__).

- *Clone* your fork onto your computer: ``git clone git@github.com:<your_github_account>/MDTF-diagnostics.git``.
  This not only downloads the files, but due to the magic of git  also gives you the full commit history of all branches.

- Enter the project directory: ``cd MDTF-diagnostics``.

- Git knows about your fork, but you need to tell it about NOAA's repo if you wish to contribute changes back to the
  code base. To do this, type ``git remote add upstream git@github.com:NOAA-GFDL/MDTF-diagnostics.git``.

Now you have two remote repos: ``origin``, your GitHub fork which you can read and write to, and ``upstream``,
NOAA's code base which you can only read from.

Another approach is to create a local repo on your machine and manage the code using the ``git`` command in a terminal.
In the interests of making things self-contained, the rest of this section gives brief step-by-step instructions
on git for interested developers.

.. _ref-new-pod:

Working on a brand new POD
--------------------------
Developers can either clone the MDTF-diagnostics repo to their computer, or manage the MDTF package using the GitHub
webpage interface.
Whichever method you choose, remember to create your [POD branch name] branch from the main branch, not the main branch.
Since developers commonly work on their own machines, this manual provides command line instructions.

1. Check out a branch for your POD

::

   git checkout -b [POD branch name]

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

   git push -u origin [POD branch name]

.. _ref-push:

Pushing to your remote POD branch on your fork
----------------------------------------------
When you are ready to push your updates to the remote POD branch on your fork

1. Type ``git status`` to list the file(s) that have been updated

2. Repeat steps 3--5 of section  (:ref:`ref-new-pod`)

.. _ref-pull-request:

Submitting Pull Requests
------------------------
The pull request (PR) for your branch is your proposal to the maintainers to incorporate your POD into NOAA's repo.
Your changes will not affect the official NOAA's repo until the PR is accepted by the lead-team programmer.
Note that if any buttons are missing, try ``CRTL`` + ``+`` or ``CRTL`` + ``-`` to adjust the webpage font size so
the missing buttons may magically appear.

To submit a PR :

#. Click the *Contribute* link on the main page of your MDTF-diagnostics fork and click the *Open Pull Request* button

#. Verify that your fork is set as the **base** repository, and *main* is set as the **base branch**,
   that *NOAA-GFDL* is set as the **head repository**, and *main* is set as the **head** branch

#. Click the *Create Pull Request* button, add a brief description to the PR header, and go through the checklist to
   ensure that your code meets that baseline requirements for review

#. Click the *Create Pull Request* button (now in the lower left corner of the message box)

   Note that you can submit a Draft Pull Request if you want to run the code through the CI, but are not ready
   for a full review by the framework team. Starting from step 3. above

#. Click the arrow on the right edge of the *Create Pull Request* button and select *Create draft pull request*
   from the dropdown menu.

#. Continue pushing changes to your POD branch until you are ready for a review (the PR will update automatically)

#. When you are ready for review, navigate to the NOAA-GFDL/MDTF-Diagnostics
   `*Pull requests* <https://github.com/NOAA-GFDL/MDTF-diagnostics/pulls>`__ page, and click on your PR

#. Scroll down to the header that states "this pull request is still a work in progress",
   and click the *ready for review* button to move the PR out of *draft* mode

.. _ref-update-main:

Updating your remote and local main branches
--------------------------------------------

Method 1: Web interface+command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
See the `MDTF Best Practices Overview <https://docs.google.com/presentation/d/18jbi50vC9X89vFbL0W1Ska1dKuW_yWY51SomWx_ahYE/edit?usp=sharing>`__
presentation for instructions with figures.

1. Click the *Fetch Upstream* link on the main page of your MDTF-diagnostics fork, then click the *Open Pull Request*
   button

2. Verify that your fork is set as the **base** repository, and *main* is set as the **base branch**,
   that *NOAA-GFDL* is set as the **head repository**, and *main* is set as the **head** branch

3. Create a title for your PR, add a description if you want, then click *Create pull request*

4. Click **Merge pull request**

Your remote main branch is now up-to-date with the NOAA-GFDL/main branch.

5. On your machine, open a terminal and check out the main branch
::

   git checkout main

6. Fetch the updates to the main branch from your remote fork
::

   git fetch

7. Pull in the updates from the remote main branch.
::

   git pull

Your local main branch is now up-to-date with the NOAA-GFDL/main branch.

Method 2: Command line only
^^^^^^^^^^^^^^^^^^^^^^^^^^^
This method requires adding the *NOAA-GFDL/MDTF-diagnostics* repo to the *.git/config* file in your local repo,
and is described in the GitHub discussion post
`Working with multiple remote repositories in your git config file <https://github.com/NOAA-GFDL/MDTF-diagnostics/discussions/96>`__.

.. _ref-merge:
Updating your POD branch by merging in changes from the main branch
-------------------------------------------------------------------
1. Create a backup copy of your repo on your machine.

2. Update the local and remote main branches on your fork as described in :ref:`ref-update-main`.

3. Check out your POD branch, and merge the main branch into your POD branch

::

   git checkout [POD branch name]
   git merge main

4. Resolve any conflicts that occur from the merge

5. Add the updated files to the staging area

::

   git add file1
   git add file2
   ...

6. Push the branch updates to your remote fork

::

   git push -u origin [POD branch name]

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

   git push origin [POD branch name]

Set up SSH with GitHub
----------------------

- You have to generate an `SSH key <https://help.github.com/en/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent>`__ and `add it <https://help.github.com/en/articles/adding-a-new-ssh-key-to-your-github-account>`__ to your GitHub account. This will save you from having to re-enter your GitHub username and password every time you interact with their servers.

- When generating the SSH key, you'll be asked to pick a *passphrase* (i.e., password).

- The following instructions assume you've generated an SSH key. If you're using manual authentication instead,
  replace the "``git@github.com:``" addresses in what follows with "``https://github.com/``".


Some online git resources
-------------------------

If you are new to git and unfamiliar with many of the terminologies, `Dangit, Git?! <https://dangitgit.com/>`__ provides solutions *in plain English* to many common mistakes people have made.

There are many comprehensive online git tutorials, such as:

- The official `git tutorial <https://git-scm.com/docs/gittutorial>`__.

- A more verbose `introduction <https://www.atlassian.com/git/tutorials/what-is-version-control>`__
  to the ideas behind git and version control.

- A still more detailed `walkthrough <http://swcarpentry.github.io/git-novice/>`__, assuming no prior knowledge.

Git Tips and Tricks
-------------------
* If you are unfamiliar with git and want to practice with the commands listed here, we recommend you to create an
  additional POD branch just for this. Remember: your changes will not affect NOAA's repo until you've submitted a pull
  request through the GitHub webpage and accepted by the lead-team programmer.

* GUI applications can be helpful when trying to resolve merge conflicts.Git packages for IDEs such as VSCode, Pycharm,
  and Eclipse often include tools for merge conflict resolution. You can also install free versions of merge-conflict
  tools like `P4merge <https://www.perforce.com/products/helix-core-apps/merge-diff-tool-p4merge>`__ and
  `Sublime merge <https://www.sublimemerge.com/>`__.

* If you encounter problems during practice, you can first try looking for *plain English* instructions to fix
  the situation at `Dangit, Git?! <https://dangitgit.com/>`__.

* A useful command is ``git status`` to remind you what branch you're on and changes you've made
  (but have not committed yet).

* ``git branch -a`` lists all branches with ``*`` indicating the branch you're on.

* Push your changes to your remote fork often (at least daily) even if your changes aren't "clean", or you are in
  the middle of a task. Your commit history does not need to look like a polished document, and nobody is judging your
  coding prowess by your development branch. Frequently pushing to your remote branch ensures that you have an easily
  accessible recent snapshot of your code in the event that your system goes down, or you go crazy with ``rm -f *``.

* A commit creates a snapshot of the code into the history in your local repo.

   - The snapshot will exist until you intentionally delete it (after confirming a warning message).
     You can always revert to a previous snapshot.

   - You'll be asked to enter a commit message. Good commit messages are key to making the project's history useful.

   - Write in *present tense* describing what the commit, when applied, does to the code -- not what you did to the code.

   - Messages should start with a brief, one-line summary, less than 80 characters. If this is too short, you may want
     to consider entering your changes as multiple commits.

* Good commit messages are key to making the project's history useful. To make this easier, instead of using the ``-m``
  flag, To provide further information, add a blank line after the summary and wrap text to 72 columns if your editor
  supports it (this makes things display nicer on some tools). Here's an
  `example <https://github.com/NOAA-GFDL/MDTF-diagnostics/commit/225b29f30872b60621a5f1c55a9f75bbcf192e0b>`__.

* To configure git to launch your text editor of choice: ``git config --global core.editor "<command string to
  launch your editor>"``.

* To set your email: ``git config --global user.email "myemail@somedomain.com"`` You can use the masked email
  Github provides if you don't want your work email included in the commit log message. The masked email address
  is located in the `Primary email address` section under Settings > emails.

* When the POD branch is no longer needed, delete the branch locally with ``git branch -d [POD branch name]``.
  If you pushed the POD branch to your fork, you can delete it remotely with
  ``git push --delete origin [POD branch name]``.

  - Remember that branches in git are just pointers to a particular commit, so by deleting a branch you *don't* lose
    any history.

* If you want to let others work on your POD, push the POD branch to your GitHub fork with
  ``git push -u origin [POD branch name``.

* For additional ways to undo changes in your branch, see
  `How to undo (almost) anything with Git <https://github.blog/2015-06-08-how-to-undo-almost-anything-with-git/>`__.
