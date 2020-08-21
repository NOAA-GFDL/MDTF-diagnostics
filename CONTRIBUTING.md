# Contributing

### Table of Contents
- [Git Policy](#git_policy)


## <a name="git_policy"></a>Git policy

### Repo Organization
Contributors are encouraged to follow the [git-flow](https://nvie.com/posts/a-successful-git-branching-model/) model, which has proven to be a popular way to organize projects. There are three permanent branches in the project:
- `main`: The "stable release" branch. At any time, a new user should be able to clone main to obtain fully functional, scientifically valid code.
- `develop`: The "beta testing" branch. 
- `hotfix`: Branch from which one-off bug fixes are committed.

All work is done in *feature branches*, which have names of the form `feature/<my_feature_name>` (note that git only allows one slash in branch names). These branch off and merge back into `develop` or other feature branches. Git's philosophy is to make branching and merging as lightweight as possible, so feature branches should have a narrow, specific scope and be short-lived.

<!--
TODO: more to say here?
-->
### Example
There are many git tutorials online, but in the interests of making things self-contained we give some step-by-step instructions here:

#### Getting started
- Create a *fork* of the project by clicking the button in the upper-right corner of the [main Github page](https://github.com/NOAA-GFDL/MDTF-diagnostics). This will create a copy in your own Github account which you have full control over.
- *Clone* your fork onto your computer: `git clone git@github.com:<your_github_account>/MDTF-diagnostics.git`. This not only downloads the files, but due to the magic of git  also gives you the full commit history of all branches.
- Enter the project directory: `cd MDTF-diagnostics`.
- Git knows about your fork, but you need to tell it about NOAA's repo if you wish to contribute changes back to the code base. To do this, type `git remote add upstream git://github.com/NOAA-GFDL/MDTF-diagnostics.git`. Now you have two remote repos: `origin`, your Github fork which you can read and write to, and `upstream`, NOAA's code base which you can only read from.
<!--
- (TODO: `pip install -v .`, other installation instructions...)
-->

#### Coding a feature
- Start from the `develop` branch: `git checkout develop`.
- If it's been a while since you created your fork, other people may have updated NOAA's `develop` branch. To make sure you're up-to-date, get these changes with `git pull upstream develop`.
- That command updates the working copy on your computer, but you also need to tell your fork on github about the changes: `git push origin develop`.
- Now you're up-to-date and ready to start working on a new feature. `git checkout -b feature/<my_feature_name>` will create a new branch (`-b` flag) off of `develop` and switch you to working on that branch.
- Write your code! Useful commands are `git status` to remind you what branch you're on and what uncommitted changes there are, and `git branch -a` to list all branches.
<!--
- (TODO: tests ...)
- (TODO: adding files...)
-->
- Commit changes with `git commit -m <your commit message>`. This means you enter a snapshot of the code base into the history in your local repo. 
    - Don't commit code that you know is buggy or non-functional!
    - Good commit messages are key to making the project's history useful. To make this easier, instead of using the `-m` flag, you can configure git to launch your text editor of choice with `git config --global core.editor "<command string to launch your editor>"`.
    - Write in the *present tense*. Commit messages should describe what the commit, when applied, does to the code -- not what you did to the code.
    - Messages should start with a brief, one-line summary, less than 80 characters. If this is too short, you may want to consider entering your changes as multiple commits.
    - To provide further information, add a blank line after the summary and wrap text to 72 columns if your editor supports it (this makes things display nicer on some tools). Here's an [example](https://github.com/NOAA-GFDL/MDTF-diagnostics/commit/225b29f30872b60621a5f1c55a9f75bbcf192e0b).
- If you want to let others work on your feature, push its branch to your github fork with `git push -u origin feature/<my_feature_name>`. The `-u` flag is for creating a new branch remotely and only needs to be used the first time.
- If you get tired of re-entering your github password, it's highly recommended you [generate an SSH key](https://help.github.com/en/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) and [add it to your github account](https://help.github.com/en/articles/adding-a-new-ssh-key-to-your-github-account).
- When your feature is finished, merge it back into `develop`: first `git checkout develop` then `git merge --no-ff feature/<my_feature_name>`. **The `--no-ff` flag is important:** it tells git not to compress ("fast-forward") your commit history onto the `develop` branch. 
- `git push origin`. 
- When your feature is ready, submit a *pull request* by going to the Github page of your fork and clicking on that button. This is your proposal to the maintainers to incorporate your feature into NOAA's code base. 
- (... policy on CI, tests passing ...)
- When it's no longer needed, delete the branch locally with `git branch -d feature/<my_feature_name>`. If you pushed it to your fork, you can delete it remotely with `git push --delete origin feature/<my_feature_name>`. Remember that branches in git are just pointers to a particular commit, so by deleting a branch you *don't* lose any history.

