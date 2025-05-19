document.addEventListener('DOMContentLoaded', function() {
    // 检查用户是否已登录
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // 显示用户信息
    const user = JSON.parse(localStorage.getItem('user'));
    if (user) {
        document.getElementById('username-display').textContent = user.username;
    }

    // 设置当前日期为默认记录日期
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('record-date').value = today;

    // 初始化模态框
    const addRecordModal = new bootstrap.Modal(document.getElementById('addRecordModal'));
    
    // 添加记录按钮
    document.getElementById('add-record-btn').addEventListener('click', function() {
        addRecordModal.show();
    });

    // 退出登录
    document.getElementById('logout-btn').addEventListener('click', logout);
    document.getElementById('logout-dropdown').addEventListener('click', logout);

    // 保存记录按钮
    document.getElementById('save-record-btn').addEventListener('click', saveRecord);

    // 计算BMI
    const weightInput = document.getElementById('weight');
    const heightInput = document.getElementById('height');
    
    function calculateBMI() {
        const weight = parseFloat(weightInput.value);
        const height = parseFloat(heightInput.value);
        
        if (weight && height) {
            const heightInMeters = height / 100;
            const bmi = weight / (heightInMeters * heightInMeters);
            
            // 计算BMI并四舍五入到小数点后一位
            return Math.round(bmi * 10) / 10;
        }
        
        return null;
    }
    
    // 当体重或身高输入改变时计算BMI
    weightInput.addEventListener('input', function() {
        const bmi = calculateBMI();
        if (bmi) {
            // 如果表单中有一个隐藏的BMI字段，可以将计算结果赋值给它
            if (document.getElementById('bmi')) {
                document.getElementById('bmi').value = bmi;
            }
        }
    });
    
    heightInput.addEventListener('input', function() {
        const bmi = calculateBMI();
        if (bmi) {
            if (document.getElementById('bmi')) {
                document.getElementById('bmi').value = bmi;
            }
        }
    });

    // 加载健康记录
    loadHealthRecords();
    
    // 加载仪表盘数据
    loadDashboardData();
});

// 退出登录
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

// 保存健康记录
async function saveRecord() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // 获取表单数据
    const formData = new FormData(document.getElementById('record-form'));
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        if (value) {
            data[key] = value;
        }
    }
    
    // 计算BMI
    if (data.weight && data.height) {
        const heightInMeters = data.height / 100;
        data.bmi = Math.round((data.weight / (heightInMeters * heightInMeters)) * 10) / 10;
    }
    
    try {
        const response = await fetch('/api/health/records', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('addRecordModal'));
            modal.hide();
            
            // 重置表单
            document.getElementById('record-form').reset();
            
            // 重新加载数据
            loadHealthRecords();
            loadDashboardData();
            
            // 显示成功消息
            alert('记录保存成功');
        } else {
            alert(`保存失败: ${result.message}`);
        }
    } catch (error) {
        console.error('保存记录错误:', error);
        alert('保存记录时发生错误，请稍后再试');
    }
}

// 加载健康记录
async function loadHealthRecords() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    try {
        const response = await fetch('/api/health/records', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayRecords(result.records);
            updateCharts(result.records);
        } else {
            console.error('加载记录失败:', result.message);
        }
    } catch (error) {
        console.error('加载记录错误:', error);
    }
}

// 显示记录
function displayRecords(records) {
    const tableBody = document.getElementById('records-table-body');
    
    if (!records || records.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" class="text-center">暂无记录</td></tr>';
        return;
    }
    
    // 最多显示最近10条记录
    const recentRecords = records.slice(0, 10);
    
    let html = '';
    
    recentRecords.forEach(record => {
        html += `
            <tr>
                <td>${formatDate(record.record_date)}</td>
                <td>${record.weight || '-'}</td>
                <td>${record.bmi || '-'}</td>
                <td>${record.blood_pressure_systolic ? `${record.blood_pressure_systolic}/${record.blood_pressure_diastolic}` : '-'}</td>
                <td>${record.heart_rate || '-'}</td>
                <td>${record.blood_sugar || '-'}</td>
                <td>${record.sleep_hours || '-'}</td>
                <td>${record.steps || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editRecord(${record.id})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteRecord(${record.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
}

// 加载仪表盘数据
function loadDashboardData() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    fetch('/api/health/records', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success && result.records.length > 0) {
            // 获取最新记录
            const latestRecord = result.records[0];
            
            // 更新BMI卡片
            if (latestRecord.bmi) {
                document.getElementById('bmi-value').textContent = latestRecord.bmi;
                let bmiStatus = 'normal';
                if (latestRecord.bmi < 18.5) {
                    bmiStatus = '偏瘦';
                } else if (latestRecord.bmi < 24) {
                    bmiStatus = '正常';
                } else if (latestRecord.bmi < 28) {
                    bmiStatus = '偏胖';
                } else {
                    bmiStatus = '肥胖';
                }
                document.getElementById('bmi-status').textContent = bmiStatus;
            }
            
            // 更新体重卡片
            if (latestRecord.weight) {
                document.getElementById('weight-value').textContent = latestRecord.weight;
                
                // 如果有历史记录，计算趋势
                if (result.records.length > 1) {
                    const previousWeight = result.records[1].weight;
                    if (previousWeight) {
                        const diff = latestRecord.weight - previousWeight;
                        let trend = '';
                        if (diff > 0) {
                            trend = `↑ 增加 ${diff.toFixed(1)} kg`;
                        } else if (diff < 0) {
                            trend = `↓ 减少 ${Math.abs(diff).toFixed(1)} kg`;
                        } else {
                            trend = '维持不变';
                        }
                        document.getElementById('weight-trend').textContent = trend;
                    } else {
                        document.getElementById('weight-trend').textContent = '无历史数据';
                    }
                } else {
                    document.getElementById('weight-trend').textContent = '首次记录';
                }
            }
            
            // 更新血压卡片
            if (latestRecord.blood_pressure_systolic && latestRecord.blood_pressure_diastolic) {
                document.getElementById('bp-value').textContent = 
                    `${latestRecord.blood_pressure_systolic}/${latestRecord.blood_pressure_diastolic}`;
                
                // 评估血压状态
                let bpStatus = '';
                const sys = latestRecord.blood_pressure_systolic;
                const dia = latestRecord.blood_pressure_diastolic;
                
                if (sys < 120 && dia < 80) {
                    bpStatus = '正常';
                } else if ((sys >= 120 && sys <= 129) && dia < 80) {
                    bpStatus = '偏高';
                } else if ((sys >= 130 && sys <= 139) || (dia >= 80 && dia <= 89)) {
                    bpStatus = '一级高血压';
                } else if (sys >= 140 || dia >= 90) {
                    bpStatus = '二级高血压';
                }
                
                document.getElementById('bp-status').textContent = bpStatus;
            }
            
            // 更新心率卡片
            if (latestRecord.heart_rate) {
                document.getElementById('hr-value').textContent = latestRecord.heart_rate;
                
                // 评估心率状态
                let hrStatus = '';
                const hr = latestRecord.heart_rate;
                
                if (hr < 60) {
                    hrStatus = '偏低';
                } else if (hr >= 60 && hr <= 100) {
                    hrStatus = '正常';
                } else {
                    hrStatus = '偏高';
                }
                
                document.getElementById('hr-status').textContent = hrStatus;
            }
        }
    })
    .catch(error => {
        console.error('加载仪表盘数据错误:', error);
    });
}

// 更新图表
function updateCharts(records) {
    if (!records || records.length === 0) {
        return;
    }
    
    // 按日期从早到晚排序（倒序）
    records = records.slice().reverse();
    
    // 准备数据
    const dates = records.map(record => formatDate(record.record_date));
    const weights = records.map(record => record.weight || null);
    const systolic = records.map(record => record.blood_pressure_systolic || null);
    const diastolic = records.map(record => record.blood_pressure_diastolic || null);
    
    // 体重图表
    const weightCtx = document.getElementById('weightChart').getContext('2d');
    new Chart(weightCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: '体重 (kg)',
                data: weights,
                borderColor: 'rgba(40, 167, 69, 1)',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
    
    // 血压图表
    const bpCtx = document.getElementById('bpChart').getContext('2d');
    new Chart(bpCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: '收缩压',
                    data: systolic,
                    borderColor: 'rgba(220, 53, 69, 1)',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    borderWidth: 2,
                    tension: 0.1
                },
                {
                    label: '舒张压',
                    data: diastolic,
                    borderColor: 'rgba(0, 123, 255, 1)',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

// 编辑记录
function editRecord(recordId) {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    // 获取记录详情
    fetch(`/api/health/records/${recordId}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            const record = result.record;
            
            // 打开模态框
            const modal = new bootstrap.Modal(document.getElementById('addRecordModal'));
            modal.show();
            
            // 填充表单
            document.getElementById('record-date').value = formatDate(record.record_date);
            if (record.weight) document.getElementById('weight').value = record.weight;
            if (record.height) document.getElementById('height').value = record.height;
            if (record.blood_pressure_systolic) document.getElementById('blood-pressure-systolic').value = record.blood_pressure_systolic;
            if (record.blood_pressure_diastolic) document.getElementById('blood-pressure-diastolic').value = record.blood_pressure_diastolic;
            if (record.heart_rate) document.getElementById('heart-rate').value = record.heart_rate;
            if (record.blood_sugar) document.getElementById('blood-sugar').value = record.blood_sugar;
            if (record.sleep_hours) document.getElementById('sleep-hours').value = record.sleep_hours;
            if (record.steps) document.getElementById('steps').value = record.steps;
            if (record.notes) document.getElementById('notes').value = record.notes;
            
            // 更改保存按钮行为
            const saveButton = document.getElementById('save-record-btn');
            saveButton.textContent = '更新记录';
            
            // 保存当前按钮的点击事件处理程序
            const originalClickHandler = saveButton.onclick;
            
            // 设置新的点击事件处理程序
            saveButton.onclick = function() {
                updateRecord(recordId);
                
                // 恢复按钮文本和原始点击事件处理程序
                saveButton.textContent = '保存记录';
                saveButton.onclick = originalClickHandler;
            };
        } else {
            alert('获取记录失败：' + result.message);
        }
    })
    .catch(error => {
        console.error('获取记录错误:', error);
        alert('获取记录时发生错误');
    });
}

// 更新记录
function updateRecord(recordId) {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    // 获取表单数据
    const formData = new FormData(document.getElementById('record-form'));
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        if (value) {
            data[key] = value;
        }
    }
    
    // 计算BMI
    if (data.weight && data.height) {
        const heightInMeters = data.height / 100;
        data.bmi = Math.round((data.weight / (heightInMeters * heightInMeters)) * 10) / 10;
    }
    
    // 发送更新请求
    fetch(`/api/health/records/${recordId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('addRecordModal'));
            modal.hide();
            
            // 重置表单
            document.getElementById('record-form').reset();
            
            // 重新加载数据
            loadHealthRecords();
            loadDashboardData();
            
            alert('记录更新成功');
        } else {
            alert('更新失败：' + result.message);
        }
    })
    .catch(error => {
        console.error('更新记录错误:', error);
        alert('更新记录时发生错误');
    });
}

// 删除记录
function deleteRecord(recordId) {
    if (!confirm('确定要删除这条记录吗？')) {
        return;
    }
    
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    fetch(`/api/health/records/${recordId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // 重新加载数据
            loadHealthRecords();
            loadDashboardData();
            
            alert('记录删除成功');
        } else {
            alert('删除失败：' + result.message);
        }
    })
    .catch(error => {
        console.error('删除记录错误:', error);
        alert('删除记录时发生错误');
    });
} 