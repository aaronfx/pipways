
export class Component {
    constructor(props = {}) {
        this.props = props;
        this.element = null;
    }

    createElement(html) {
        const div = document.createElement('div');
        div.innerHTML = html.trim();
        this.element = div.firstChild;
        this.bindEvents();
        return this.element;
    }

    bindEvents() {
        // Override in subclasses
    }

    render() {
        throw new Error('Render method must be implemented');
    }
}
