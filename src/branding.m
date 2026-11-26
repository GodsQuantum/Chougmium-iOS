#import <UIKit/UIKit.h>
#import <objc/runtime.h>

static id (*originalNewTab)(id,SEL,id);
static void (*originalAbout)(id,SEL);

static id brandedNewTab(id self,SEL cmd,id browser) {
    id page=originalNewTab(self,cmd,browser);
    Ivar logo=page ? class_getInstanceVariable([page class],"_logo") : NULL;
    UILabel *label=logo ? object_getIvar(page,logo) : nil;
    if ([label isKindOfClass:[UILabel class]] && [label.text isEqualToString:@"Venetium"])
        label.text=@"Chougmium";
    return page;
}

static void brandedAbout(id self,SEL cmd) {
    originalAbout(self,cmd);
    if (![self isKindOfClass:[UITableViewController class]]) return;
    UIView *header=[(UITableViewController *)self tableView].tableHeaderView;
    for (UIView *view in header.subviews) {
        if ([view isKindOfClass:[UILabel class]] && [((UILabel *)view).text isEqualToString:@"Venetium"])
            ((UILabel *)view).text=@"Chougmium";
    }
}

// Only the two audited upstream UI classes, no global UILabel hook.
static IMP install(Class cls,SEL sel,IMP replacement) {
    if (!cls) return NULL;
    Method m=class_getInstanceMethod(cls,sel);
    if (!m) return NULL;
    IMP prior=method_getImplementation(m);
    if (!class_addMethod(cls,sel,replacement,method_getTypeEncoding(m)))
        method_setImplementation(m,replacement);
    return prior;
}

__attribute__((constructor))
static void brand(void) {
    originalNewTab=(id (*)(id,SEL,id))install(objc_getClass("VINewTabPage"),@selector(initWithBrowser:),(IMP)brandedNewTab);
    originalAbout=(void (*)(id,SEL))install(objc_getClass("VIAboutList"),@selector(viewDidLayoutSubviews),(IMP)brandedAbout);
}
