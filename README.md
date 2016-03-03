# Overview

This charm is used to deploy fiche, the open source pastebin behind termbin.


This charm provides [fiche](https://github.com/solusipse/fiche). Command line pastebin for sharing terminal output.

# Usage

To deploy fiche using juju:

    juju deploy fiche

You can then use netcat to do things like 
    
```bash
cat file.txt | nc <ficheserver> <port>
```

# Configuration

Once you have deployed fiche you can add an alias to your .bashrc to make fiche slightly more usable:

```bash
echo 'alias tb="nc <ficheserver> <port>"' >> .bashrc
```

Then you can:

```bash
echo less typing now! | tb
```

# Contact Information

- James Beedy <jamesbeedy@gmail.com>
- http://termbin.com/
- https://github.com/solusipse/fiche
