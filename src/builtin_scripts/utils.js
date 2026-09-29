export class ScrollInfo {
    constructor (left, top) {
        this.left = left;
        this.top = top;
    }

}

export function getScrollPosition() {
    return new ScrollInfo(window.scrollX, window.scrollY)
}

export function setScrollPosition(left, top) {
    console.log(`Scroll to ${left}, ${top}`)
    window.scrollTo(left, top)
}

