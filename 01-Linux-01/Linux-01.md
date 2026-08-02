# Linux Important Commands and Notes for Data Practitioners 

[toc]

## Enabling WSL 2 (recommended for Windows 11)

1. Right-click on the Windows Start menu icon, choose *Search* and type ***Windows Features***. Select the top entry (category *Control panel*) to enable or turn off Windows-Features. The Windows-Features dialog will be opened.
2. Select in the upcoming dialog the two check boxes for ***Windows Subsystem for Linux*** and for ***Virtual Machine Platform*** and press the *OK* button. Applying the changes may take a few minutes. Finally, press the *Restart now* button to reboot the computer.
3. On some Windows installations WSL must be updated, before the Linux distribution can be installed. We recommend therefore to open a command window and enter the command: **`wsl --update`** to update the WSL. Finally, reboot the computer. after the update is finished.

> ✅ Stronlgy Recommend to Install [(New) PowerShell](https://learn.microsoft.com/en-us/powershell/scripting/install/install-powershell).

🔗 [Reference](https://www.ridom.de/u/Windows_Subsystem_For_Linux.html)

![](.\Screens\Windws-Feature.png)



![](.\Screens\Wsl-Activation.png)



## Common Operating Systems (OS)

We have three main OS; **Windows, Linux** and **Mac.** 

- Windows is suitable for daily jobs.
- Linux and Mac are more focused on Programming and other professional stuffs.  



## Why Linux?

• Open Source Operating System (OS)
• Eagerly chosen by programmers. Why?
	– It’s free
	– More secure, it will protect your systems from trojans, viruses, adware etc.
	– Easy to customize
	– Variety of distribution: Ubuntu, Fedora and many more…
• Linux is heavily documented
• Over 1000 commands, but I will present you some of the most common ones in daily basis.



> 1️⃣ **Technically: Linux is just the Kernel**
> The **kernel** is the core part of the operating system. It is the software that talks directly to your hardware (CPU, RAM, disk drives) and manages resources.
>
> 2️⃣ **A Linux distribution** **Consist of**:
> **The Linux Kernel** + **GNU utilities** (shell, compilers, file managers) + **Graphical interface** + **Package manager** + **Application software** (browsers, office suites).
>
> 3️⃣ **An operating system**:
> Is the master software that controls your hardware (CPU, RAM, disk drives, network card). When you run Ubuntu on WSL, **it does not control your hardware**. So, Ubuntu on WSL is just a **guest environment**.
>
> 4️⃣ **When we could say Linux is an OS?**
> A full distribution installed on its own bare-metal machine, VM, or cloud instance; Now this is an **OS**.



## An Important Note

In Linux and all Unix-based OS (like Mac) we have `/`  (**forward slash**) in our file system. But in Windows OS we have `\` (**back slash**).

```bash
.\others\st-app\spark ===> Windows 
./others/st-ap/spark ===> Linux
```



## Some useful cli commands for interacting with wsl

```bash
# Will list all wsl distros for us
wsl -l -v

# Set the default wsl distro
wsl --set-version Ubuntu-24.04

# Show us a list of available distros. OR YOU CAN USE "Microsoft Store".
wsl -l --online

# Install for us the Debian distro
wsl --install -d Debian
```

> Mine 👇👇👇
>
> ```powershell
> PS C:\Users\User> wsl -l -v
>   NAME              STATE           VERSION
> * Ubuntu            Running         2
>   docker-desktop    Stopped         2
> ```



## Some Linux commands!

### 1- `cd` Command (Change Directory)

• **Change directory** from your current position
• Probably the most common command in linux
• You can pass DIRECTORY as relative or absolute path

```bash
cd ~/absolute/path/to/Directory

cd relative/path/to/Directory

cd Directory

# Move to home directory (the same behaviour as cd alone)
cd ~ 

# Move one directory up, can be used multiple time, for example cd ../../../
cd ../ 

# Move to previously used directory
cd - 

# MOve to the root directory
cd /
```



### 2- `cat` Command

• **Display content** of file/s on the standard output
• Possible to display a content of one, multiple file and to concatenate content of different files together using `>` **"redirect"** and `>>`  **"append"** operators.

**Examples:**

```bash
#display content of file.txt in the terminal
cat file.txt

#display content of both, first file1.txt and second file2.txt
cat file1.txt file2.txt

#concatenate two files and save it as a new file called combined_files.txt with `>` operator, which is used for output redirection
cat file1.txt file2.txt > combined_files.txt

#add additional.txt content at the end of existing.txt file, `>>` operator is used for appending output.
cat additional.txt >> existing.txt
```



### 3- `echo` Command

• **Display** text or variables **as output**, it is commonly used in shell scripts.
• It is often used in shell scripting to display messages, debug scripts, or generate dynamic output

**Examples:**

```bash
# Print “Hello, world” in the terminal
echo "Hello, world!”

# Print “My name is John” in the terminal
name="John”
echo "My name is $name"

# Will copy "My name is John" string into text.txt file
echo "My name is $name" > text.txt
```



### 4- `man` COMMAND

• man is an interface to the on-line reference manuals, it is used to display the manual pages (documentation) for various commands, programs, and system functions
• It provides detailed information about command usage, options, syntax, and examples
**Example:**

```bash
#display manual page for the `find` command
man find
```



### 5- `ls` Command (List)

• **List** files and directories on current or given directory. The second most known command.

**Examples:**

```bash
# list all files including hidden files.
ls –a

# list with long format.
ls -l

# recursively list subdirectories.
ls –R

#list files in given path.
ls path/to/Directory

#list files in given directories.
ls path/to/Directory1 path/to/Directory2
```



### 6- `pwd` Command (Print Working Directory)

• **find** the path to current working directory. Useful inside scripts to specify absolute path.

**Example:**

```bash
# print current location
pwd

#to print current location
echo "Your current location is: $(pwd)”
```



### 7- `mkdir` Command (Make Directory)

• Make directories much faster than with manual clicking. 

**Examples:**

```bash
# creates a directory called “new_directory”.
mkdir new_directory

#will create 3 new directories if none of them already exist.
mkdir –p new/intermediate/dirs

OUTPUT 👇👇👇
amin@Mohammad-Fozouni:~$ tree ./new
./new
└── intermediate
    └── dirs

3 directories, 0 files
```



### 8- `cp` Command (Copy)

• **Copy** files or directories with their content wherever you want.

**Examples:**

```bash
# copy file.txt and paste it to /home/files directory
cp file.txt /home/files

# copy file1,2,3 to /home/files/ directory
cp file1.txt file2.txt file3.txt /home/files

# copy file1.txt and create a copy file2.txt in the same directory
cp file1.txt file2.txt

# copy photos directory to destination dir
cp –R /home/files/photos /home/files/destination
```



### 9- `mv` Command (Move)

• **Rename or move files** and directories with their content from one destination to another.

**Examples:**

```bash
# rename file.txt to renamed_file.txt
mv file.txt renamed_file.txt 

#move file.txt to files directory
mv file.txt /home/files/ 

# move multiple files simultaneously
mv file1.txt file2.txt /home/files/
```



### 10- `rm` Command (Removes)

• **Remove file, files or directories** with their content depending on syntax being used.

**Examples:**

```bash
amin@Mohammad-Fozouni:$ mkdir testdirectory ; touch testdirectory/test.txt
amin@Mohammad-Fozouni:$ ls
testdirectory
amin@Mohammad-Fozouni:$ rm testdirectory/
rm: cannot remove 'testdirectory/': Is a directory
amin@Mohammad-Fozouni:$ rm -r testdirectory/
```



### 11- `touch` Command

• **Create** an empty file or generate and modify a timestamp.
**Example:**

```bash
# create a new fille called file.txt in the current directory, if the file exists command WILL updates the file’s timestamp to the current time without modyfing its content
touch file.txt
```



### 12- `tar` Command

• Create, manipulate and extract files from tape archives (tar files) with optional compression.

**Examples:**

```bash
# Create a tar archive from some files:
tar -cvf archive.tar file1.txt file2.txt

# Extract files from a tar archive:
tar -xvf archive.tar

# Extract files from a tar archive to a specific directory:
tar -xvf archive.tar -C /path/to/destination

# Compress files while creating a tar archive:
tar -czvf archive.tar.gz directory
```



### 13- `grep` Command (Global, Rgular Expression, Print)

• One of the most useful commands, especially while dealing with a lot of text data, for example log files. Print lines matching a pattern, it lets you find a pattern by searching through all the texts in a specific file.

**Examples:**

```bash
# Finds all lines containing "error" in the system log file.
grep "error" /var/log/syslog

# Searches for "TODO" in every file inside the projects folder and its subfolders.
rep -r "TODO" ~/projects/

# Searches for warning without case sensetivity in app.log file
grep -in "warning" app.log

# -i = ignore case (matches "warning", "WARNING", "Warning")
# -n = show line numbers

# Sample Output 👇👇👇
45:WARNING: Disk space low
89:warning: Connection timeout
```



### 14- `history` Command

• List up to 1000 of previously executed commands (we can change it). 

**Examples:**

```bash
#display a numbered list of previously executed commands in the terminal
history

#clear the command history
history -c
```



------

### 15- `chmod` Command (Change Mode)

• It enable modifying a file or directory’s read, write, and execute permissions. Often used in shell scripting or command-line operations to set permissions on files or directories.

Every actions has an special number as follows:

- read = 4

- write = 2

- execute = 1

**Examples:**

```bash
# Add executable permission to the script.sh file
chmod +x script.sh 

# Set read and write permissions for the owner, and read-only permissions for others on the file.txt
chmod 644 file.txt 

#Recursively set full permissions (read, write, execute) for all users on the directory and its contents
chmod -R 777 directory
```

• chmod assigns permissions using three numbers: the first number represents permissions
for the **owner**, the second number for the **group**, and the third number for **others**
(<OWNER><GROUP><OTHERS>): 

- **`u`** = **user** or the **owner** of the file
- `g` = **group**
- `o` = **others** (everyone else)

```bash
chmod u=rwx, g=rw, o=r /home/amin

chmod 764 /home/amin
```



### 16- `wget` Command ("World-Wide-Web" and "get")

• The non-interactive network downloader, it retrieves files using HTTP, HTTPS, and FTP protocols. Often used to download files, web pages, or entire websites from remote servers.

**Examples:**

```bash
#Download the file.txt from the specified URL
wget https://example.com/file.txt

#Download the entire website from the specified URL, recursively
wget -r -np https://example.com

#Download the file.txt from the specified URL and save it as output.txt
wget -O output.txt https://example.com/file.txt
```



### 17- `sudo` Command (Superuser Do)

• Used as a prefix for some commands that only superusers are allowed to run. Often used in
command-line operations to run commands that require elevated permissions.

**Examples:**

```bash
# Run the 'apt update' command with administrative privileges to update package information.
sudo apt update

# Delete a directory and its contents with administrative permissions.
sudo rm -rf /path/to/directory

# Create a new user account with administrative privileges.
sudo useradd newuser

# change from current user to root
sudo su
```



### 18- `alias` Command

• This command allows you to create custom shortcuts or abbreviations (aliases) for frequently used
commands or command sequences.

```bash
# From now on, if we type c it will work as clear command
alias c='clear'
```



### 19- `passwd` Command (Password)

• The passwd command is used to change or update user passwords in Linux systems. It allows users to manage their own passwords or enables system administrators to modify user passwords.

**Examples:**

```bash
# Change the password for the current user.
passwd

# Change the password for the specified user (requires administrative privileges).
passwd username

# Lock the specified user account by disabling the password.
passwd -l username

# Unlock the specified user account by enabling the password.
passwd -u username

# Force the specified user to change their password during the next login.
passwd -e username

# Remove the password for the specified user, making it passwordless.
passwd -d username

# Display password-related information for the specified user.
passwd -S username
```



### 20- `ssh` Command (Secure Shell)

• The ssh command (Secure Shell) is used to establish secure, encrypted remote connections to Linux
servers or devices. It provides a secure method for logging into and executing commands on remote
machines.

**Examples:**

```bash
# Connect to the remote host specified by hostname using the username.
ssh username@hostname

# Connect to the remote host using a non-default SSH port
ssh -p port username@hostname

# Connect using a specific private key file instead of the default key
ssh -i private_key_file username@hostname
```



### 21- `SCP` Command (Secure Copy Protocol)

We use scp command to securly copy files between servers or computers.

**Examples:**

```bash
scp -i /path/to/private_key /path/to/local/file username@server_ip:/path/to/remote/destination/

scp mydocument.txt root@192.168.1.100:/home/root/
```



## Each and Everyday:

• To navigate through system I need to **change [cd] directories** all the time.
• I need to know what can I find so I need to **list [ls] files** and directories.
• To pack and unpack tarball files I am using **[tar –xzvf / -czvf]** frequently.
• To login to external server **[ssh]** is my guy.



## Some useful links:

1. Go to https://www.m-fozouni.ir/alias-in-windows-and-linux/ if you want to see how we can set aliases permanently in Windows.
2. You can browse this page https://www.m-fozouni.ir/blog/ for which I regularly write about different things in the world of **DE, DS and ML(Sec)Ops**.