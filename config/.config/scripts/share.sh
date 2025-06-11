#!/bin/bash
sudo mount -t 9p -o trans=virtio,version9p2000.L kvm_shared /mnt/kvm_shared
ln -s /mnt/kvm_shared/ ~/kvm_shared
