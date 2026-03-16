/**
 * courses.js v2 — Complete LMS Module
 * Features: Course Listing, Course Detail, Lesson Viewer, Quiz System
 */

const CoursesPage = {
    currentCourse: null,
    currentLesson: null,
    
    async render(containerId = 'app') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // Default view: Course Listing
        await this.renderCourseList(container);
    },
    
    async renderCourseList(container) {
        container.innerHTML = `
            <div class="max-w-7xl mx-auto">
                <div class="flex justify-between items-center mb-6">
                    <div>
                        <h2 class="text-2xl font-bold text-white">📚 Trading Academy</h2>
                        <p class="text-gray-400 text-sm mt-1">Master the markets with structured courses</p>
                    </div>
                </div>
                <div id="courses-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div class="col-span-full text-center py-12">
                        <i class="fas fa-spinner fa-spin text-3xl text-purple-400 mb-3"></i>
                        <p class="text-gray-400">Loading courses...</p>
                    </div>
                </div>
            </div>
        `;
        
        try {
            const courses = await dashboard.apiRequest('/courses/list');
            const grid = document.getElementById('courses-grid');
            
            if (!courses || courses.length === 0) {
                grid.innerHTML = `
                    <div class="col-span-full text-center py-12">
                        <i class="fas fa-graduation-cap text-4xl text-gray-600 mb-3 block"></i>
                        <p class="text-gray-400">No courses available yet</p>
                    </div>
                `;
                return;
            }
            
            grid.innerHTML = courses.map(course => this.createCourseCard(course)).join('');
            
        } catch (error) {
            console.error('[Courses] Error loading courses:', error);
            container.innerHTML = `
                <div class="text-center py-12">
                    <i class="fas fa-exclamation-triangle text-3xl text-red-400 mb-3"></i>
                    <p class="text-gray-400">Failed to load courses</p>
                    <button onclick="CoursesPage.render()" class="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg">
                        Retry
                    </button>
                </div>
            `;
        }
    },
    
    createCourseCard(course) {
        const progress = course.progress || 0;
        const hasProgress = progress > 0;
        const isCompleted = progress === 100;
        
        return `
            <div class="bg-gray-800 rounded-xl overflow-hidden border border-gray-700 hover:border-purple-500/50 transition-all hover:transform hover:-translate-y-1 group cursor-pointer"
                 onclick="CoursesPage.viewCourse(${course.id})">
                <div class="relative h-48 overflow-hidden">
                    ${course.thumbnail_url 
                        ? `<img src="${course.thumbnail_url}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" onerror="this.src='/static/default-course.jpg'">`
                        : `<div class="w-full h-full bg-gradient-to-br from-purple-900 to-blue-900 flex items-center justify-center">
                             <i class="fas fa-graduation-cap text-6xl text-white/20"></i>
                           </div>`
                    }
                    ${isCompleted 
                        ? `<div class="absolute top-3 right-3 bg-green-500 text-white px-2 py-1 rounded-full text-xs font-bold">
                             <i class="fas fa-check mr-1"></i>Completed
                           </div>`
                        : hasProgress 
                            ? `<div class="absolute top-3 right-3 bg-purple-500 text-white px-2 py-1 rounded-full text-xs font-bold">
                                 ${progress}%
                               </div>`
                            : ''
                    }
                    ${course.price > 0 
                        ? `<div class="absolute top-3 left-3 bg-yellow-500 text-black px-2 py-1 rounded-full text-xs font-bold">
                             $${course.price}
                           </div>`
                        : `<div class="absolute top-3 left-3 bg-green-500 text-white px-2 py-1 rounded-full text-xs font-bold">FREE</div>`
                    }
                </div>
                <div class="p-5">
                    <div class="flex items-center gap-2 mb-2">
                        <span class="text-xs font-semibold px-2 py-0.5 rounded bg-gray-700 text-gray-300">${course.level || 'Beginner'}</span>
                        <span class="text-xs text-gray-500">${course.module_count || 0} modules • ${course.lesson_count || 0} lessons</span>
                    </div>
                    <h3 class="text-lg font-bold text-white mb-2 line-clamp-1">${course.title}</h3>
                    <p class="text-sm text-gray-400 line-clamp-2 mb-4 h-10">${course.description || 'No description available'}</p>
                    
                    ${hasProgress ? `
                        <div class="mb-3">
                            <div class="flex justify-between text-xs text-gray-400 mb-1">
                                <span>Progress</span>
                                <span>${progress}%</span>
                            </div>
                            <div class="w-full bg-gray-700 rounded-full h-2">
                                <div class="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all" style="width: ${progress}%"></div>
                            </div>
                        </div>
                    ` : ''}
                    
                    <button class="w-full py-2.5 rounded-lg font-semibold text-sm transition-colors ${
                        isCompleted 
                            ? 'bg-green-600/20 text-green-400 border border-green-600/50 hover:bg-green-600/30'
                            : hasProgress
                                ? 'bg-purple-600 text-white hover:bg-purple-700'
                                : 'bg-gray-700 text-white hover:bg-gray-600'
                    }">
                        ${isCompleted ? 'Review Course' : hasProgress ? 'Continue Learning →' : 'Start Learning →'}
                    </button>
                </div>
            </div>
        `;
    },
    
    async viewCourse(courseId) {
        const container = document.getElementById('app') || document.getElementById('section-courses');
        if (!container) return;
        
        container.innerHTML = `
            <div class="max-w-5xl mx-auto">
                <div class="mb-6">
                    <button onclick="CoursesPage.render()" class="text-gray-400 hover:text-white text-sm mb-4 flex items-center gap-2">
                        <i class="fas fa-arrow-left"></i> Back to Courses
                    </button>
                    <div id="course-header" class="bg-gray-800 rounded-xl p-6 border border-gray-700">
                        <div class="flex items-center justify-center h-32">
                            <i class="fas fa-spinner fa-spin text-3xl text-purple-400"></i>
                        </div>
                    </div>
                </div>
                <div id="curriculum-container" class="space-y-4">
                    <div class="bg-gray-800 rounded-xl p-8 border border-gray-700 text-center">
                        <i class="fas fa-spinner fa-spin text-2xl text-purple-400 mb-2"></i>
                        <p class="text-gray-400">Loading curriculum...</p>
                    </div>
                </div>
            </div>
        `;
        
        try {
            const data = await dashboard.apiRequest(`/courses/${courseId}/curriculum`);
            this.currentCourse = data.course;
            
            // Render header
            const header = document.getElementById('course-header');
            header.innerHTML = `
                <div class="flex flex-col md:flex-row gap-6">
                    ${data.course.thumbnail 
                        ? `<img src="${data.course.thumbnail}" class="w-full md:w-48 h-32 object-cover rounded-lg">`
                        : `<div class="w-full md:w-48 h-32 bg-gradient-to-br from-purple-900 to-blue-900 rounded-lg flex items-center justify-center">
                             <i class="fas fa-graduation-cap text-4xl text-white/30"></i>
                           </div>`
                    }
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="text-xs font-semibold px-2 py-0.5 rounded bg-gray-700 text-gray-300">${data.course.level || 'Beginner'}</span>
                        </div>
                        <h1 class="text-2xl font-bold text-white mb-2">${data.course.title}</h1>
                        <p class="text-gray-400 text-sm mb-4">${data.course.description || ''}</p>
                        <div class="flex items-center gap-4 text-sm text-gray-500">
                            <span><i class="fas fa-layer-group mr-1"></i> ${data.modules.length} modules</span>
                            <span><i class="fas fa-book mr-1"></i> ${data.modules.reduce((acc, m) => acc + (m.lessons?.length || 0), 0)} lessons</span>
                        </div>
                    </div>
                </div>
            `;
            
            // Render curriculum (Modules → Lessons → Quiz)
            const container = document.getElementById('curriculum-container');
            if (data.modules.length === 0) {
                container.innerHTML = `
                    <div class="bg-gray-800 rounded-xl p-8 border border-gray-700 text-center">
                        <i class="fas fa-folder-open text-4xl text-gray-600 mb-3"></i>
                        <p class="text-gray-400">No content available for this course yet</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = data.modules.map((module, idx) => `
                <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                    <div class="p-4 bg-gray-700/50 border-b border-gray-700 flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white font-bold text-sm">
                                ${idx + 1}
                            </div>
                            <div>
                                <h3 class="font-semibold text-white">${module.title}</h3>
                                <p class="text-xs text-gray-400">${module.lessons?.length || 0} lessons ${module.quiz ? '• 1 quiz' : ''}</p>
                            </div>
                        </div>
                        <i class="fas fa-chevron-down text-gray-500"></i>
                    </div>
                    <div class="divide-y divide-gray-700">
                        ${(module.lessons || []).map((lesson, lidx) => `
                            <div onclick="CoursesPage.viewLesson(${courseId}, ${lesson.id}, ${module.id})" 
                                 class="p-4 hover:bg-gray-700/30 cursor-pointer flex items-center justify-between group">
                                <div class="flex items-center gap-3">
                                    <div class="w-6 h-6 rounded-full ${lesson.completed ? 'bg-green-500' : 'bg-gray-600'} flex items-center justify-center">
                                        ${lesson.completed 
                                            ? '<i class="fas fa-check text-white text-xs"></i>'
                                            : `<span class="text-white text-xs">${lidx + 1}</span>`
                                        }
                                    </div>
                                    <div>
                                        <p class="text-sm font-medium text-white group-hover:text-purple-400 transition-colors">${lesson.title}</p>
                                        <p class="text-xs text-gray-500">
                                            ${lesson.duration_minutes > 0 ? `<i class="fas fa-clock mr-1"></i>${lesson.duration_minutes}m` : ''}
                                            ${lesson.is_free_preview ? '<span class="text-green-400 ml-2">Free Preview</span>' : ''}
                                        </p>
                                    </div>
                                </div>
                                <i class="fas fa-play-circle text-gray-600 group-hover:text-purple-400"></i>
                            </div>
                        `).join('')}
                        
                        ${module.quiz ? `
                            <div onclick="CoursesPage.startQuiz(${courseId}, ${module.quiz.id})" 
                                 class="p-4 hover:bg-gray-700/30 cursor-pointer flex items-center justify-between group bg-yellow-900/10">
                                <div class="flex items-center gap-3">
                                    <div class="w-6 h-6 rounded-full bg-yellow-600 flex items-center justify-center">
                                        <i class="fas fa-question text-white text-xs"></i>
                                    </div>
                                    <div>
                                        <p class="text-sm font-medium text-yellow-400">Module Quiz: ${module.quiz.title}</p>
                                        <p class="text-xs text-gray-500">Passing score: ${module.quiz.pass_percentage}%</p>
                                    </div>
                                </div>
                                <i class="fas fa-chevron-right text-yellow-600"></i>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `).join('');
            
        } catch (error) {
            console.error('[Courses] Error loading course:', error);
            container.innerHTML = `
                <div class="bg-gray-800 rounded-xl p-8 border border-gray-700 text-center">
                    <i class="fas fa-exclamation-triangle text-3xl text-red-400 mb-3"></i>
                    <p class="text-gray-400">Failed to load course content</p>
                    <button onclick="CoursesPage.viewCourse(${courseId})" class="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg">
                        Retry
                    </button>
                </div>
            `;
        }
    },
    
    async viewLesson(courseId, lessonId, moduleId) {
        // Create modal overlay
        const modal = document.createElement('div');
        modal.id = 'lesson-modal';
        modal.className = 'fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-gray-800 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                <div class="p-4 border-b border-gray-700 flex items-center justify-between">
                    <div>
                        <h3 class="font-bold text-white" id="lesson-title">Loading...</h3>
                        <p class="text-xs text-gray-400" id="lesson-module">Module ${moduleId}</p>
                    </div>
                    <button onclick="document.getElementById('lesson-modal').remove()" class="text-gray-400 hover:text-white">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
                <div class="flex-1 overflow-y-auto p-4" id="lesson-content">
                    <div class="flex items-center justify-center h-64">
                        <i class="fas fa-spinner fa-spin text-3xl text-purple-400"></i>
                    </div>
                </div>
                <div class="p-4 border-t border-gray-700 flex items-center justify-between bg-gray-700/30">
                    <button onclick="CoursesPage.prevLesson()" class="px-4 py-2 text-gray-400 hover:text-white disabled:opacity-50" id="btn-prev" disabled>
                        <i class="fas fa-arrow-left mr-2"></i>Previous
                    </button>
                    <button onclick="CoursesPage.markComplete(${courseId}, ${lessonId})" class="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold" id="btn-complete">
                        <i class="fas fa-check mr-2"></i>Mark Complete
                    </button>
                    <button onclick="CoursesPage.nextLesson()" class="px-4 py-2 text-gray-400 hover:text-white disabled:opacity-50" id="btn-next" disabled>
                        Next<i class="fas fa-arrow-right ml-2"></i>
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        try {
            // Fetch lesson details from curriculum data we already have
            const curriculum = await dashboard.apiRequest(`/courses/${courseId}/curriculum`);
            let lesson = null;
            let module = null;
            
            for (const m of curriculum.modules) {
                const l = m.lessons.find(l => l.id === lessonId);
                if (l) {
                    lesson = l;
                    module = m;
                    break;
                }
            }
            
            if (!lesson) throw new Error('Lesson not found');
            
            document.getElementById('lesson-title').textContent = lesson.title;
            document.getElementById('lesson-module').textContent = module.title;
            
            const contentDiv = document.getElementById('lesson-content');
            
            // Video player
            let videoHtml = '';
            if (lesson.video_url) {
                if (lesson.video_url.includes('youtube.com') || lesson.video_url.includes('youtu.be')) {
                    const videoId = lesson.video_url.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/)?.[1];
                    if (videoId) {
                        videoHtml = `<iframe class="w-full aspect-video rounded-lg mb-4" src="https://www.youtube.com/embed/${videoId}" frameborder="0" allowfullscreen></iframe>`;
                    }
                } else if (lesson.video_url.includes('vimeo.com')) {
                    const videoId = lesson.video_url.match(/vimeo\.com\/(\d+)/)?.[1];
                    if (videoId) {
                        videoHtml = `<iframe class="w-full aspect-video rounded-lg mb-4" src="https://player.vimeo.com/video/${videoId}" frameborder="0" allowfullscreen></iframe>`;
                    }
                } else {
                    videoHtml = `<video class="w-full rounded-lg mb-4" controls><source src="${lesson.video_url}" type="video/mp4"></video>`;
                }
            }
            
            contentDiv.innerHTML = `
                ${videoHtml}
                <div class="prose prose-invert max-w-none">
                    <h4 class="text-lg font-semibold text-white mb-2">Lesson Content</h4>
                    <p class="text-gray-300 leading-relaxed">${lesson.content || 'No content available for this lesson.'}</p>
                </div>
                ${lesson.attachment_url ? `
                    <div class="mt-4 p-4 bg-gray-700/30 rounded-lg flex items-center gap-3">
                        <i class="fas fa-paperclip text-purple-400 text-xl"></i>
                        <div class="flex-1">
                            <p class="text-sm font-medium text-white">Attachment</p>
                            <a href="${lesson.attachment_url}" target="_blank" class="text-sm text-purple-400 hover:underline">Download Resource</a>
                        </div>
                    </div>
                ` : ''}
            `;
            
            // Update navigation buttons
            const allLessons = curriculum.modules.flatMap(m => m.lessons);
            const currentIndex = allLessons.findIndex(l => l.id === lessonId);
            
            document.getElementById('btn-prev').disabled = currentIndex === 0;
            document.getElementById('btn-next').disabled = currentIndex === allLessons.length - 1;
            
            // Store for navigation
            this.currentLesson = {
                courseId,
                lessonId,
                allLessons,
                currentIndex
            };
            
            // Update complete button if already completed
            if (lesson.completed) {
                const btn = document.getElementById('btn-complete');
                btn.innerHTML = '<i class="fas fa-check-double mr-2"></i>Completed';
                btn.classList.remove('bg-green-600', 'hover:bg-green-700');
                btn.classList.add('bg-gray-600', 'cursor-default');
                btn.disabled = true;
            }
            
        } catch (error) {
            console.error('[Courses] Error loading lesson:', error);
            document.getElementById('lesson-content').innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-exclamation-triangle text-3xl text-red-400 mb-2"></i>
                    <p class="text-gray-400">Failed to load lesson</p>
                </div>
            `;
        }
    },
    
    async markComplete(courseId, lessonId) {
        const btn = document.getElementById('btn-complete');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
        
        try {
            const result = await dashboard.apiRequest(`/courses/${courseId}/lessons/${lessonId}/complete`, {
                method: 'POST'
            });
            
            btn.innerHTML = '<i class="fas fa-check-double mr-2"></i>Completed';
            btn.classList.remove('bg-green-600', 'hover:bg-green-700');
            btn.classList.add('bg-gray-600', 'cursor-default');
            
            // Show success notification
            dashboard._toast?.('Lesson completed!', 'success');
            
            // If course completed, show certificate notification
            if (result.course_completed) {
                setTimeout(() => {
                    alert(`🎉 Congratulations! You've completed the course!\nCertificate ID: ${result.certificate_id || 'N/A'}`);
                }, 500);
            }
            
        } catch (error) {
            console.error('[Courses] Error marking complete:', error);
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-check mr-2"></i>Mark Complete';
            alert('Failed to save progress. Please try again.');
        }
    },
    
    prevLesson() {
        if (!this.currentLesson || this.currentLesson.currentIndex <= 0) return;
        const prev = this.currentLesson.allLessons[this.currentLesson.currentIndex - 1];
        this.viewLesson(this.currentLesson.courseId, prev.id, prev.module_id);
    },
    
    nextLesson() {
        if (!this.currentLesson || this.currentLesson.currentIndex >= this.currentLesson.allLessons.length - 1) return;
        const next = this.currentLesson.allLessons[this.currentLesson.currentIndex + 1];
        this.viewLesson(this.currentLesson.courseId, next.id, next.module_id);
    },
    
    async startQuiz(courseId, quizId) {
        const modal = document.createElement('div');
        modal.id = 'quiz-modal';
        modal.className = 'fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-gray-800 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                <div class="p-4 border-b border-gray-700 flex items-center justify-between">
                    <h3 class="font-bold text-white">Quiz</h3>
                    <button onclick="document.getElementById('quiz-modal').remove()" class="text-gray-400 hover:text-white">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="flex-1 overflow-y-auto p-6" id="quiz-content">
                    <div class="flex items-center justify-center h-32">
                        <i class="fas fa-spinner fa-spin text-2xl text-purple-400"></i>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        try {
            const quiz = await dashboard.apiRequest(`/courses/${courseId}/quizzes/${quizId}`);
            
            const content = document.getElementById('quiz-content');
            content.innerHTML = `
                <h2 class="text-xl font-bold text-white mb-2">${quiz.title}</h2>
                <p class="text-sm text-gray-400 mb-6">Passing score: ${quiz.pass_percentage}% • ${quiz.questions.length} questions</p>
                
                <form id="quiz-form" class="space-y-6">
                    ${quiz.questions.map((q, idx) => `
                        <div class="bg-gray-700/30 rounded-lg p-4">
                            <p class="font-medium text-white mb-3"><span class="text-purple-400 mr-2">${idx + 1}.</span>${q.question}</p>
                            <div class="space-y-2">
                                ${['a', 'b', 'c', 'd'].filter(opt => q[`option_${opt}`]).map(opt => `
                                    <label class="flex items-center gap-3 p-3 rounded-lg bg-gray-700/50 hover:bg-gray-700 cursor-pointer transition-colors">
                                        <input type="radio" name="q${q.id}" value="${opt}" class="w-4 h-4 text-purple-500" required>
                                        <span class="text-gray-300">${q[`option_${opt}`]}</span>
                                    </label>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                    
                    <button type="submit" class="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold">
                        Submit Quiz
                    </button>
                </form>
            `;
            
            document.getElementById('quiz-form').onsubmit = async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const answers = {};
                formData.forEach((val, key) => {
                    answers[key.replace('q', '')] = val;
                });
                
                // Submit
                const btn = e.target.querySelector('button[type="submit"]');
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Submitting...';
                
                try {
                    const result = await dashboard.apiRequest(`/courses/${courseId}/quizzes/${quizId}/submit`, {
                        method: 'POST',
                        body: JSON.stringify(answers)
                    });
                    
                    this.showQuizResults(result, quiz);
                } catch (err) {
                    alert('Failed to submit quiz: ' + err.message);
                    btn.disabled = false;
                    btn.innerHTML = 'Submit Quiz';
                }
            };
            
        } catch (error) {
            console.error('[Courses] Error loading quiz:', error);
            document.getElementById('quiz-content').innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-exclamation-triangle text-3xl text-red-400 mb-2"></i>
                    <p class="text-gray-400">Failed to load quiz</p>
                </div>
            `;
        }
    },
    
    showQuizResults(result, quiz) {
        const content = document.getElementById('quiz-content');
        const passed = result.passed;
        
        content.innerHTML = `
            <div class="text-center mb-6">
                <div class="inline-flex items-center justify-center w-20 h-20 rounded-full ${passed ? 'bg-green-500/20' : 'bg-red-500/20'} mb-4">
                    <span class="text-3xl ${passed ? 'text-green-400' : 'text-red-400'} font-bold">${result.score}%</span>
                </div>
                <h3 class="text-xl font-bold ${passed ? 'text-green-400' : 'text-red-400'} mb-1">
                    ${passed ? '🎉 Congratulations! You Passed!' : '❌ Quiz Failed'}
                </h3>
                <p class="text-gray-400 text-sm">You got ${result.correct_count} out of ${result.total_questions} correct</p>
            </div>
            
            <div class="space-y-3 mb-6">
                ${result.results.map((r, idx) => `
                    <div class="flex items-start gap-3 p-3 rounded-lg ${r.is_correct ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}">
                        <div class="mt-0.5">
                            ${r.is_correct 
                                ? '<i class="fas fa-check-circle text-green-400"></i>'
                                : '<i class="fas fa-times-circle text-red-400"></i>'
                            }
                        </div>
                        <div class="flex-1">
                            <p class="text-sm font-medium text-white">Question ${idx + 1}</p>
                            <p class="text-xs text-gray-400">Your answer: ${r.user_answer.toUpperCase()} ${!r.is_correct ? `• Correct: ${r.correct_answer.toUpperCase()}` : ''}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <div class="flex gap-3">
                ${!passed ? `
                    <button onclick="CoursesPage.startQuiz(${this.currentCourse?.id || 0}, ${quiz.id})" class="flex-1 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold">
                        Retry Quiz
                    </button>
                ` : `
                    <button onclick="document.getElementById('quiz-modal').remove()" class="flex-1 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold">
                        Continue Learning
                    </button>
                `}
                <button onclick="document.getElementById('quiz-modal').remove()" class="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg">
                    Close
                </button>
            </div>
        `;
    }
};

// Make available globally
window.CoursesPage = CoursesPage;
