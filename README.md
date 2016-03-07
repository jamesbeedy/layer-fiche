# Overview

This charm is used to deploy fiche, the open source pastebin behind termbin.


This charm provides [fiche](https://github.com/solusipse/fiche). Command line pastebin for sharing terminal output.

# Usage

To deploy fiche using juju:

    juju deploy fiche

This will deploy fiche server to listen on port 9999 by default. 

You can then use netcat to do things like
    
```bash
cat file.txt | nc <ficheserver> 9999
```

# Configuration

Once you have deployed fiche you can add an alias to your .bashrc to make fiche slightly more usable:

```bash
echo 'alias tb="nc <ficheserver> 9999"' >> .bashrc
```

Then you can:

```bash
echo less typing now! | tb
```

# Contact Information

- James Beedy <jamesbeedy@gmail.com>
- http://termbin.com/
- https://github.com/solusipse/fiche
