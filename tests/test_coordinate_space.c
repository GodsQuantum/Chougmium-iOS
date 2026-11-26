#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <objc/runtime.h>

void vi_install_coordinate_space(void);

static int have_window = 1;
static int have_selector = 1;
static int method_exists = 0;
static int add_count = 0;
static IMP registered_imp = 0;

Class objc_getClass(const char *name) {
  assert(strcmp(name, "UIWindow") == 0);
  return have_window ? (Class)0x10 : NULL;
}
SEL sel_registerName(const char *name) {
  assert(strcmp(name, "coordinateSpace") == 0);
  return have_selector ? (SEL)0x20 : NULL;
}
Method class_getInstanceMethod(Class cls, SEL sel) {
  assert(cls == (Class)0x10 && sel == (SEL)0x20);
  return method_exists ? (Method)0x30 : NULL;
}
BOOL class_addMethod(Class cls, SEL sel, IMP imp, const char *types) {
  assert(cls == (Class)0x10 && sel == (SEL)0x20);
  assert(strcmp(types, "@@:") == 0);
  add_count++;
  registered_imp = imp;
  method_exists = 1;
  return 1;
}

int main(void) {
  id window = (id)0x1234;
  SEL sel = (SEL)0x20;
  vi_install_coordinate_space();
  assert(add_count == 1 && registered_imp);
  assert(registered_imp(window, sel) == window);
  vi_install_coordinate_space();
  assert(add_count == 1);  /* idempotent */
  method_exists = 1;
  vi_install_coordinate_space();
  assert(add_count == 1);  /* native method preserved */
  method_exists = 0;
  have_window = 0;
  vi_install_coordinate_space();
  assert(add_count == 1);  /* missing UIKit class -> fail closed */
  have_window = 1;
  have_selector = 0;
  vi_install_coordinate_space();
  assert(add_count == 1);  /* missing selector -> fail closed */
  puts("PASS: missing method added only once; native preserved; fallback is window itself");
  return 0;
}

