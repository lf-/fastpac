# List of mirrors to use
#mirrorlist = get_mirrorlist_online("https://www.archlinux.org/mirrors/status/json/")
# Default location looks at mirrors in /etc/pacman.d/mirrorlist
mirrorlist = get_mirrorlist_offline()

# This contains repos and their package databases.
databases = download_repos(["core", "extra", "community", "multilib"], mirrorlist)

# What mirror should the package be downloaded from? There are a variety of preimplement ways in
# fastpac.mirrorlist. Some implementations will run out of mirrorrs to select from if not enough
# are present. This one will chose the mirror that has been used the least, taking into account
# package size. CapPicker will assign a virtual cap to each mirror.
mirrorpicker = LeastUsedPicker(mirrorlist)

# Directory which the agents on remote systems put their package lists in
package_list_dir = '/var/cache/fastpac/packagelists'

# Destination of downloads
download_dir = '/var/cache/fastpac/pkg'

# Optional: operating system architecture
# architecture = 'x86_64'

workers = 4
