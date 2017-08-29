# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 16:14:15 2017

@author: Local_Admin
"""

import thorlabs_apt as apt
apt.list_available_devices()
#%%
motor = apt.Motor(27502020)
