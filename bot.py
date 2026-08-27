  function renderNotificationsPage() {
    const sortedNotifications = [...notifications].reverse();
    
    return `
        <div class="page-enter">
            <div class="p-20 text-center">
                <h2>الإشعارات</h2>
            </div>
            ${sortedNotifications.length > 0 ? sortedNotifications.map(notif => `
                <div class="ios-card" style="${notif.read ? 'opacity:0.7;' : ''}">
                    <h4>${notif.title}</h4>
                    <p class="mt-5">${notif.body}</p>
                    <small style="color:var(--text-secondary); display:block; margin-top:10px;">${formatDate(notif.timestamp)}</small>
                    ${!notif.read ? '<span style="display:inline-block; background:var(--primary); color:white; padding:2px 8px; border-radius:10px; font-size:10px; margin-top:5px;">جديد</span>' : ''}
                </div>
            `).join('') : '<p class="text-center mt-20">لا توجد إشعارات</p>'}
        </div>
    `;
}
