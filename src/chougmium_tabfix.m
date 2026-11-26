// Chougmium interim UIKit repair, independent of the Blink engine.
// One rootful MobileSubstrate filter: ru.computershik.venetium.
#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import <objc/runtime.h>

static void (*originalGridReload)(id, SEL);
static void (*originalMenuShow)(id, SEL, UIView *, CGRect, id);
static char browserAssociationKey;
static char menuAssociationKey;

@protocol CGTabBrowser <NSObject>
- (id)selectedTab;
- (void)closeTab:(id)tab;
@end

@interface CGCloseControls : NSObject <UIGestureRecognizerDelegate>
- (void)closeCurrentTab:(UIButton *)sender;
@end

@implementation CGCloseControls

- (BOOL)gestureRecognizer:(UIGestureRecognizer *)recognizer shouldReceiveTouch:(UITouch *)touch {
    // A tap on the X is a button tap, not "select this tab".
    // Avoid invoking two mutually exclusive actions on the same contact.
    UIView *view = touch.view;
    while (view != nil && view != recognizer.view) {
        if ([view isKindOfClass:[UIControl class]]) {
            return NO;
        }
        view = view.superview;
    }
    return YES;
}

- (void)closeCurrentTab:(UIButton *)sender {
    id<CGTabBrowser> browser =
        (id<CGTabBrowser>)objc_getAssociatedObject(sender, &browserAssociationKey);
    UIView *menu = (UIView *)objc_getAssociatedObject(sender, &menuAssociationKey);
    if (![browser respondsToSelector:@selector(closeTab:)] ||
        ![browser respondsToSelector:@selector(selectedTab)]) {
        return;
    }
    id tab = [browser selectedTab];
    [menu removeFromSuperview]; // Mirror VIMenu's normal dismissThen behavior.
    if (tab != nil) {
        [browser closeTab:tab]; // Original browser code manages last-tab fallback.
    }
}
@end

static CGCloseControls *sharedControls(void) {
    static CGCloseControls *controls;
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        controls = [[CGCloseControls alloc] init];
    });
    return controls;
}

static void fixedGridReload(id grid, SEL command) {
    if (originalGridReload) {
        originalGridReload(grid, command);
    }
    // The original tab card installs a UITapGestureRecognizer around a UIButton.
    // Its default cancellation can prevent UIControlEventTouchUpInside.
    UIView *root = (UIView *)grid;
    for (UIView *child in root.subviews) {
        if (![child isKindOfClass:[UIScrollView class]]) {
            continue;
        }
        for (UIView *card in child.subviews) {
            if (![NSStringFromClass([card class]) isEqualToString:@"VITabCard"]) {
                continue;
            }
            for (UIGestureRecognizer *gesture in card.gestureRecognizers) {
                if ([gesture isKindOfClass:[UITapGestureRecognizer class]]) {
                    gesture.delegate = sharedControls();
                    gesture.cancelsTouchesInView = NO;
                }
            }
        }
    }
}

static void attachCloseTabRow(UIView *menu, id browser) {
    Class menuClass = objc_getClass("VIMenu");
    if (!menuClass || ![menu isKindOfClass:menuClass]) {
        return;
    }
    Ivar cardIvar = class_getInstanceVariable(menuClass, "_card");
    if (!cardIvar) {
        return; // Fail closed if a future upstream version changes its layout.
    }
    UIView *card = (UIView *)object_getIvar(menu, cardIvar);
    if (![card isKindOfClass:[UIView class]]) {
        return;
    }

    UIScrollView *list = nil;
    for (UIView *subview in card.subviews) {
        if ([subview isKindOfClass:[UIScrollView class]]) {
            list = (UIScrollView *)subview;
            break;
        }
    }
    if (!list) {
        return;
    }
    const CGFloat rowHeight = 48.0; // Original VIMenu kItemHeight.
    for (UIView *row in list.subviews) {
        if ([row isKindOfClass:[UIControl class]]) {
            CGRect frame = row.frame;
            frame.origin.y += rowHeight;
            row.frame = frame;
        }
    }

    UIButton *close = [UIButton buttonWithType:UIButtonTypeCustom];
    close.frame = CGRectMake(0, 4, list.bounds.size.width, rowHeight);
    NSString *preferred = [[NSLocale preferredLanguages] firstObject];
    BOOL french = [preferred hasPrefix:@"fr"];
    [close setTitle:(french ? @"Fermer l'onglet" : @"Close tab")
          forState:UIControlStateNormal];
    close.titleLabel.font = [UIFont systemFontOfSize:16];
    [close setTitleColor:[UIColor colorWithRed:0.78 green:0.16 blue:0.20 alpha:1]
               forState:UIControlStateNormal];
    close.contentHorizontalAlignment = UIControlContentHorizontalAlignmentLeft;
    close.contentEdgeInsets = UIEdgeInsetsMake(0, 56, 0, 8);
    close.accessibilityLabel = french ? @"Fermer l'onglet courant" : @"Close current tab";
    close.accessibilityIdentifier = @"chougmium.close-current-tab";
    objc_setAssociatedObject(close, &browserAssociationKey, browser,
                             OBJC_ASSOCIATION_ASSIGN); // App-level owner.
    objc_setAssociatedObject(close, &menuAssociationKey, menu,
                             OBJC_ASSOCIATION_ASSIGN); // Row is menu-owned.
    [close addTarget:sharedControls()
              action:@selector(closeCurrentTab:)
    forControlEvents:UIControlEventTouchUpInside];
    [list addSubview:close];
    CGSize size = list.contentSize;
    size.height += rowHeight;
    list.contentSize = size;
}

static void fixedMenuShow(id menuClass, SEL command,
                          UIView *view, CGRect anchor, id browser) {
    if (originalMenuShow) {
        originalMenuShow(menuClass, command, view, anchor, browser);
    }
    Class cls = objc_getClass("VIMenu");
    if (!cls) {
        return;
    }
    // VIMenu installs itself synchronously as the newest view child.
    for (UIView *candidate in [view.subviews reverseObjectEnumerator]) {
        if ([candidate isKindOfClass:cls]) {
            attachCloseTabRow(candidate, browser);
            break;
        }
    }
}

__attribute__((constructor))
static void initializeChougmiumTabFix(void) {
    Class grid = objc_getClass("VITabGrid");
    Class menu = objc_getClass("VIMenu");
    if (grid) {
        Method reload = class_getInstanceMethod(grid, @selector(reload));
        if (reload) {
            originalGridReload = (void (*)(id, SEL))
                method_setImplementation(reload, (IMP)fixedGridReload);
        }
    }
    if (menu) {
        Method show = class_getClassMethod(menu,
                                          @selector(showInView:anchor:browser:));
        if (show) {
            originalMenuShow = (void (*)(id, SEL, UIView *, CGRect, id))
                method_setImplementation(show, (IMP)fixedMenuShow);
        }
    }
}
