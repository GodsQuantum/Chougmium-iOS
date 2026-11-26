ARCHS = armv7
TARGET = iphone:clang:10.3:9.0
TWEAK_NAME = VenetiumUIKitCompat
VenetiumUIKitCompat_FILES = src/coordinate_space.c src/branding.m
VenetiumUIKitCompat_CFLAGS = -std=c11 -Wall -Wextra -Werror -fvisibility=hidden
VenetiumUIKitCompat_LIBRARIES = objc
VenetiumUIKitCompat_FRAMEWORKS = UIKit Foundation
VenetiumUIKitCompat_LDFLAGS = -Wl,-segalign,4000
include $(THEOS)/makefiles/common.mk
include $(THEOS_MAKE_PATH)/tweak.mk

