import { Component } from '../components/Component.js';
import { Sidebar } from '../components/Sidebar.js';
import { api } from '../api/client.js';
import { showLoading } from '../utils/helpers.js';

export class CoursesPage extends Component {
    async render() {
        const container = document.createElement('div');
        container.className = 'main-app';
        
        const sidebar = new Sidebar();
        container.appendChild(sidebar.render());
        
        const main = document.createElement('main');
        main.className = 'main-content';
        main.innerHTML = `
            <div class="page-header">
                <h2><i class="fas fa-graduation-cap" style="color: var(--primary);"></i> Trading Courses</h2>
                <p>Learn from professional traders</p>
            </div>
            
            <div id="courses-list" class="courses-grid">
                <p class="text-secondary">Loading courses...</p>
            </div>
        `;
        
        container.appendChild(main);
        this.element = container;
        
        // Load courses after render
        setTimeout(() => this.loadCourses(), 0);
        
        return container;
    }

    async loadCourses() {
        const container = this.element?.querySelector('#courses-list');
        if (!container) return;
        
        try {
            showLoading(true, 'Loading courses...');
            const data = await api.getCourses();
            
            if (data?.courses?.length > 0) {
                container.innerHTML = data.courses.map(course => `
                    <div class="course-card card">
                        <div class="course-thumbnail">
                            <img src="${course.thumbnail || '/assets/course-default.jpg'}" alt="${course.title}">
                        </div>
                        <div class="course-content">
                            <h3>${course.title}</h3>
                            <p>${course.description || ''}</p>
                            <div class="course-meta">
                                <span class="badge badge-primary">${course.level || 'Beginner'}</span>
                                <span class="text-secondary">${course.duration_hours || 0} hours</span>
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<p class="text-secondary">No courses available yet.</p>';
            }
        } catch (error) {
            console.error('Failed to load courses:', error);
            if (container) {
                container.innerHTML = '<p class="text-danger">Failed to load courses. Please try again.</p>';
            }
        } finally {
            showLoading(false);
        }
    }
}
