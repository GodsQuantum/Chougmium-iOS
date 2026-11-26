#ifndef VI_OBJC_RUNTIME_MOCK_H
#define VI_OBJC_RUNTIME_MOCK_H
typedef void* Class;
typedef void* SEL;
typedef void* Method;
typedef void* id;
typedef id (*IMP)(id, SEL);
typedef signed char BOOL;
Class objc_getClass(const char *);
SEL sel_registerName(const char *);
Method class_getInstanceMethod(Class, SEL);
BOOL class_addMethod(Class, SEL, IMP, const char *);
#endif

