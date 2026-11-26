#include <objc/runtime.h>

/* UIWindow already conforms to UICoordinateSpace on iOS 9; it has no
   separate -coordinateSpace getter. Chromium's iOS port expects one. */
static id vi_window_coordinate_space(id window, SEL command) {
  (void)command;
  return window;
}

void vi_install_coordinate_space(void) {
  Class window = objc_getClass("UIWindow");
  if (!window) return;
  SEL selector = sel_registerName("coordinateSpace");
  if (!selector || class_getInstanceMethod(window, selector)) return;
  class_addMethod(window, selector, (IMP)vi_window_coordinate_space, "@@:");
}

#ifndef VENETIUM_UNIT_TEST
__attribute__((constructor))
static void vi_initialize_compatibility(void) {
  vi_install_coordinate_space();
}
#endif

