document.addEventListener('DOMContentLoaded', function() {
    // ตัวแปรสำหรับเก็บข้อมูลมังงะ
    let mangaData = [];
    let filteredData = [];
    let currentPage = 1;
    const itemsPerPage = 10; // แสดง 10 เรื่องต่อหน้า
    
    // ฟังก์ชันสำหรับใช้ CORS proxy กับรูปภาพ
    function getProxyImageUrl(originalUrl) {
        // ใช้ localhost แทนชื่อ service เพื่อหลีกเลี่ยงปัญหา ERR_NAME_NOT_RESOLVED
        return `https://cors-proxy.supakorn.xyz/proxy-image?url=${encodeURIComponent(originalUrl)}`;
    }

    // DOM Elements
    const mangaGrid = document.getElementById('mangaGrid');
    const pagination = document.getElementById('pagination');
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const loadFileBtn = document.getElementById('loadFileBtn');
    const fileInput = document.getElementById('fileInput');
    const downloadOfficialBtn = document.getElementById('downloadOfficialBtn');
    const loader = document.getElementById('loader');
    const emptyState = document.getElementById('emptyState');
    const filterItems = document.querySelectorAll('.filter-item');
    const modal = document.getElementById('detailModal');
    const closeModal = document.getElementById('closeModal');
    const totalMangaEl = document.getElementById('totalManga');
    const avgChaptersEl = document.getElementById('avgChapters');
    const maxChaptersEl = document.getElementById('maxChapters');
    const setupInstructions = document.getElementById('setupInstructions');
    const modalImage = document.getElementById('modalImage');

    // Event Listeners
    loadFileBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);
    downloadOfficialBtn.addEventListener('click', downloadOfficialData);
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });
    closeModal.addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });

    // เพิ่ม Event Listener สำหรับตัวกรอง
    filterItems.forEach(item => {
        item.addEventListener('click', () => {
            // ลบคลาส active จากทุกไอเทม
            filterItems.forEach(i => i.classList.remove('active'));
            // เพิ่มคลาส active ให้กับไอเทมที่คลิก
            item.classList.add('active');
            // กรองข้อมูลตามเงื่อนไข
            filterManga(item.dataset.filter);
        });
    });

    // ฟังก์ชันจัดการการอัพโหลดไฟล์
    function handleFileUpload(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const rawData = JSON.parse(e.target.result);
                    mangaData = normalizeData(rawData);
                    updateStats();
                    filterManga('all');
                    hideInstructions();
                } catch (error) {
                    alert('เกิดข้อผิดพลาดในการอ่านไฟล์ JSON');
                }
            };
            reader.readAsText(file);
        }
    }

    // ฟังก์ชันแปลงข้อมูลให้เป็นรูปแบบมาตรฐาน
    function normalizeData(rawData) {
        return rawData.map(manga => {
            // ตรวจสอบรูปแบบข้อมูล
            const normalizedManga = { ...manga };

            // กรณีที่เป็นข้อมูลจากเว็บใหม่ (มังงะญี่ปุ่น.com)
            if (manga.chapter_text && !manga.chapter_count) {
                normalizedManga.chapter_count = manga.chapter || 0;
            } 
            // กรณีที่เป็นข้อมูลจากเว็บเก่า (oremanga.net)
            else if (!manga.chapter_text && manga.chapter_count) {
                normalizedManga.chapter_text = `Chapter ${manga.chapter}`;
            }

            return normalizedManga;
        });
    }

    // ฟังก์ชันซ่อนคำแนะนำ
    function hideInstructions() {
        setupInstructions.style.display = 'none';
    }

    // ฟังก์ชันอัพเดทสถิติ
    function updateStats() {
        if (mangaData.length === 0) return;

        totalMangaEl.textContent = mangaData.length;
        
        // ใช้ chapter_count หรือ chapter ตามที่มี
        const totalChapters = mangaData.reduce((sum, manga) => {
            const chapterCount = manga.chapter_count || manga.chapter || 0;
            return sum + chapterCount;
        }, 0);
        
        const avgChapters = Math.round(totalChapters / mangaData.length);
        avgChaptersEl.textContent = avgChapters;

        // หาตอนล่าสุดที่มากที่สุด (chapter ล่าสุด)
        const maxChapters = Math.max(...mangaData.map(manga => manga.chapter || 0));
        maxChaptersEl.textContent = maxChapters;
    }

    // ฟังก์ชันกรองมังงะ
    function filterManga(filter) {
        if (filter === 'all') {
            filteredData = [...mangaData];
        } else {
            const minChapters = parseInt(filter);
            filteredData = mangaData.filter(manga => {
                const chapterCount = manga.chapter_count || manga.chapter || 0;
                return chapterCount >= minChapters;
            });
        }
        currentPage = 1;
        renderMangaGrid();
        renderPagination();
    }

    // ฟังก์ชันค้นหามังงะ
    function handleSearch() {
        const searchTerm = searchInput.value.toLowerCase();
        filteredData = mangaData.filter(manga => 
            manga.name.toLowerCase().includes(searchTerm)
        );
        currentPage = 1;
        renderMangaGrid();
        renderPagination();
    }

    // ฟังก์ชันแสดงผลการ์ดมังงะ
    function renderMangaGrid() {
        if (filteredData.length === 0) {
            emptyState.style.display = 'block';
            mangaGrid.innerHTML = '';
            pagination.innerHTML = '';
            return;
        }

        emptyState.style.display = 'none';
        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        const mangaToShow = filteredData.slice(start, end);

        mangaGrid.innerHTML = mangaToShow.map(manga => {
            // ตั้งค่า URL รูปภาพผ่าน proxy เพื่อแก้ปัญหา CORS
            const originalImageUrl = manga.image_url || `https://via.placeholder.com/300x200?text=${encodeURIComponent(manga.name)}`;
            const proxyImageUrl = getProxyImageUrl(originalImageUrl);
            
            // ใช้ข้อมูลที่มี
            const chapterText = manga.chapter_text || `Chapter ${manga.chapter}`;
            const chapterCount = manga.chapter_count || manga.chapter || 0;
            
            // แสดงข้อความจำนวนตอนเฉพาะเมื่อมีข้อมูล
            const chapterCountText = chapterCount ? `ทั้งหมด ${chapterCount} ตอน` : '';
            
            return `
            <div class="manga-card" onclick="showMangaDetails('${encodeURIComponent(JSON.stringify(manga))}')">
                <div class="manga-card-img" style="background-image: url('${proxyImageUrl}')"></div>
                <div class="manga-card-content">
                    <h3 class="manga-title">${manga.name}</h3>
                    <div class="manga-info">
                        <span>ตอนที่ ${manga.chapter || 'N/A'}</span>
                        <span>${chapterCountText}</span>
                    </div>
                    <div class="card-actions">
                        <a href="${manga.link}" class="card-btn card-btn-primary" target="_blank">
                            <i class="fas fa-book-open"></i> อ่านตอนล่าสุด
                        </a>
                        <a href="${manga.profile_link}" class="card-btn card-btn-secondary" target="_blank">
                            <i class="fas fa-info-circle"></i> ดูหน้าโปรไฟล์
                        </a>
                    </div>
                </div>
            </div>
        `}).join('');
    }

    // ฟังก์ชันแสดงผล pagination
    function renderPagination() {
        const totalPages = Math.ceil(filteredData.length / itemsPerPage);
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let paginationHTML = '';
        
        // ปุ่มย้อนกลับ
        if (currentPage > 1) {
            paginationHTML += `
                <div class="pagination-item" onclick="changePage(${currentPage - 1})">
                    <i class="fas fa-chevron-left"></i>
                </div>
            `;
        }

        // ตัวเลขหน้า
        for (let i = 1; i <= totalPages; i++) {
            if (
                i === 1 || 
                i === totalPages || 
                (i >= currentPage - 2 && i <= currentPage + 2)
            ) {
                paginationHTML += `
                    <div class="pagination-item ${i === currentPage ? 'active' : ''}" 
                         onclick="changePage(${i})">
                        ${i}
                    </div>
                `;
            } else if (
                i === currentPage - 3 || 
                i === currentPage + 3
            ) {
                paginationHTML += `
                    <div class="pagination-item">
                        ...
                    </div>
                `;
            }
        }

        // ปุ่มถัดไป
        if (currentPage < totalPages) {
            paginationHTML += `
                <div class="pagination-item" onclick="changePage(${currentPage + 1})">
                    <i class="fas fa-chevron-right"></i>
                </div>
            `;
        }

        pagination.innerHTML = paginationHTML;
    }

    // ฟังก์ชันเปลี่ยนหน้า
    window.changePage = function(page) {
        currentPage = page;
        renderMangaGrid();
        renderPagination();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // ฟังก์ชันแสดงรายละเอียดมังงะในโมดัล
    window.showMangaDetails = function(mangaDataStr) {
        const manga = JSON.parse(decodeURIComponent(mangaDataStr));
        
        // ตั้งค่าหัวข้อ
        document.getElementById('modalTitle').textContent = manga.name;
        
        // ตั้งค่ารูปภาพผ่าน proxy
        const originalImageUrl = manga.image_url || `https://via.placeholder.com/300x200?text=${encodeURIComponent(manga.name)}`;
        const proxyImageUrl = getProxyImageUrl(originalImageUrl);
        modalImage.style.backgroundImage = `url('${proxyImageUrl}')`;
        
        // ใช้ข้อมูลที่มี
        const chapterText = manga.chapter_text || `Chapter ${manga.chapter || 'N/A'}`;
        const chapterCount = manga.chapter_count || manga.chapter || 0;
        
        // ตั้งค่ารายละเอียด
        const modalDetails = document.getElementById('modalDetails');
        modalDetails.innerHTML = `
            <div class="detail-row">
                <div class="detail-label">จำนวนตอน:</div>
                <div class="detail-value">${chapterCount ? `${chapterCount} ตอน` : 'ไม่ระบุ'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">ตอนล่าสุด:</div>
                <div class="detail-value">${chapterText}</div>
            </div>
        `;
        
        // ตั้งค่าลิงก์
        document.getElementById('modalReadBtn').href = manga.link;
        document.getElementById('modalProfileBtn').href = manga.profile_link;
        
        // แสดงโมดัล
        modal.style.display = 'flex';
    };

    // ฟังก์ชันดาวน์โหลดข้อมูลทางการ
    async function downloadOfficialData() {
        try {
            loader.style.display = 'block';
            const response = await fetch('https://raw.githubusercontent.com/1REDfriend/manga-find/main/manga_results.json');
            if (!response.ok) {
                throw new Error('ไม่สามารถดาวน์โหลดข้อมูลได้');
            }
            const rawData = await response.json();
            mangaData = normalizeData(rawData);
            updateStats();
            filterManga('all');
            hideInstructions();
            loader.style.display = 'none';
        } catch (error) {
            console.error('Error downloading official data:', error);
            alert('เกิดข้อผิดพลาดในการดาวน์โหลดข้อมูล: ' + error.message);
            loader.style.display = 'none';
        }
    }

    // โหลดข้อมูลเริ่มต้นจากไฟล์ JSON
    try {
        fetch('manga_results.json')
            .then(response => {
                if (!response.ok) {
                    throw new Error('ไม่พบไฟล์ manga_results.json');
                }
                return response.json();
            })
            .then(rawData => {
                mangaData = normalizeData(rawData);
                updateStats();
                filterManga('all');
                hideInstructions();
            })
            .catch(error => {
                console.error('Error loading local manga data:', error);
                emptyState.style.display = 'block';
            });
    } catch (error) {
        console.error('Error loading initial manga data:', error);
        emptyState.style.display = 'block';
    }
}); 