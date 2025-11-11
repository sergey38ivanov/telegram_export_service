document.addEventListener("DOMContentLoaded", async () => {
    const folderList = document.getElementById("folder-list");
    const chatListSidebar = document.querySelector("#chat-list ul");
    const contactTableBody = document.querySelector("#contacts.section tbody");
    const contactSection = document.querySelector("#contacts-list.section ul");
    const chatTableBody = document.querySelector("#chat-table tbody");
    const chatMessagesSection = document.getElementById("messages-container");

    const toggleBtns = document.querySelectorAll(".toggle-btn");
    toggleBtns.forEach(btn => {
        btn.addEventListener("click", () => {
        const targetId = btn.dataset.target;
        const target = document.getElementById(targetId);
        if (target.classList.contains("collapsed")) {
            target.classList.remove("collapsed");
            btn.innerText = "«";
        } else {
            target.classList.add("collapsed");
            btn.innerText = "»";
        }
        });
    });

    let selectedFolder = folderList.dataset.folder || "";
    if (selectedFolder && selectedFolder !== "None") {
        console.log(`Selected folder: ${selectedFolder}`);
        await loadFolderData(`data/${selectedFolder}`);
    }

    async function loadJSON(path) {
        const response = await fetch(path);
        return await response.json();
    }
    
    // 🗂 Список папок
    const folders = folderList.querySelectorAll("li");
    console.log('Список папок',folders);
    console.log(`Found ${folders.length} folders`);
    folders.forEach(li => {
        li.addEventListener("click", () => {
            const folderPath = `data/${li.innerText.split(" ")[1]}`;
            console.log(`Loading folder: ${folderPath}`);
            loadFolderData(folderPath);
        });
    });

    async function loadFolderData(folderPath) {
        const summary = await loadJSON(`${folderPath}/chat_summary.json`);
        const contacts = await loadJSON(`${folderPath}/contacts/contacts.json`);
        
        console.log(summary);
        console.log(contacts);
        if (!summary || !contacts) {
            console.error("Не вдалося завантажити дані для папки:", folderPath);
            return;
        }
        // 📊 Загальна інформація
        totalContacts.innerText = summary.total_contacts;
        personalChats.innerText = summary.total_personal_chats;
        publicGroups.innerText = summary.total_public_groups;
        publicChannels.innerText = summary.total_public_channels;
        privateGroups.innerText = summary.total_private_groups;
        privateCchannels.innerText = summary.total_private_channels;
        

        // 👤 Контакти
        contactTableBody.innerHTML = "";
        contactSection.innerHTML = "";

        contacts.forEach(contact => {
            let user_pic_id = randInt(1, 8)
            let name = contact.first_name || "" + " " + (contact.last_name || "");
            let profileLogo = name ? name.split(" ").slice(0, 2) : ["?"];
            profileLogo = profileLogo.map(name => isLetter(name[0])?name[0].toUpperCase():"").join("");
            
            let username = contact.username? ("@" + contact.username) : "";
            if (username) {
                username = `<a href="https://t.me/${contact.username}" target="_blanc">${username}</a>`;
            } else {
                username = "-";}

            const TR = document.createElement("tr");
            TR.classList.add("contact-item");
            TR.dataset.contactId = contact.user_id;
            TR.innerHTML = `<td><span class="photo userpic${user_pic_id}">
            <span class="profile-logo">${profileLogo}</span>
            </span></td>
            <td><span class="name">${name === " "? "-": name}</span></td>
            <td><span class="phone">${("+" + contact.phone_number) || "-"}</span></td>
            <td><span class="username">${username}</span></td>
            <td><span class="user-id">${contact.user_id}</span></td>`
            contactTableBody.appendChild(TR);
            
            const LI = document.createElement("li");
            LI.classList.add("contact-item");
            LI.dataset.contactId = contact.user_id;
            LI.innerHTML = `<span class="photo userpic${user_pic_id}">
              <span class="profile-logo">${profileLogo}</span>
            </span><span>
            <span class="name">${name === " "? "-": name}</span>
            <span class="phone">${("+" + contact.phone_number) || "-"}</span>
            </span><span>
            <span class="username">${username}</span>
            <span class="user-id">${contact.user_id}</span></span>`;
            contactSection.appendChild(LI);
        });

        // 💬 Чати
        chatListSidebar.innerHTML = "";
        chatTableBody.innerHTML = "";

        summary.personal_chats.forEach((chat, idx) => {
            const LI = document.createElement("li");
            LI.classList.add("chat-item");
            LI.dataset.chatId = idx + 1;

            let profileLogo = chat.chat_name ? chat.chat_name.split(" ").slice(0, 2) : ["?"];
            profileLogo = profileLogo.map(name => isLetter(name[0])?name[0].toUpperCase():"").join("");
            let user_pic_id = randInt(1, 8)
            LI.innerHTML = `<span class="photo userpic${user_pic_id}">
              <span class="profile-logo">${profileLogo}</span>
            </span>
            <span>
              <span>
                <span class="name">${chat.chat_name}</span>
                <span class="message-count">${chat.message_count} messages</span>
              </span>
              <span class="last-message">${chat.last_activity.replace("T", " ")}</span>
              <span class="short-chat-details">📷 ${chat.photos} 📄 ${chat.documents} 🎬 ${chat.videos} 🎵 ${chat.audios} 🎥 ${chat.video_messages} 🎤 ${chat.voice_messages}</span>
            </span>`
            LI.addEventListener("click", () => loadChat(`${folderPath}/${chat.directory}`, chat.message_count, chat));
            chatListSidebar.appendChild(LI);

            const TR = document.createElement("tr");
            TR.innerHTML = `<td><span class="photo userpic${user_pic_id}">
              <span class="profile-logo">${profileLogo}</span>
            </span></td>
            <td>${chat.chat_name}</td>
            <td>${chat.user_id}</td>
            <td>${chat.chat_type}</td>
            <td>${chat.last_activity.replace("T", " ")}</td>
            <td>💬 ${chat.message_count} 📷 ${chat.photos} 📄 ${chat.documents} 🎬 ${chat.videos} 🎵 ${chat.audios} 🎥 ${chat.video_messages} 🎤 ${chat.voice_messages}</td>`
            TR.addEventListener("click", () => loadChat(`${folderPath}/${chat.directory}`, chat.message_count, chat));
            chatTableBody.appendChild(TR);
        });
    }

    async function loadChat(folderPath, message_count, chatMeta) {
        // const files = await fetch(`${folderPath}/`).then(r => r.text());
        // const resultFile = Array.from(files.matchAll(/result_\d+\.json/g))
        // .map(m => m[0])
        // .find(name => name.includes(chatId.toString()));
        // if (!resultFile) return;
        let resultIds = [1]
        if (message_count > 1000) {
            resultIds = Array.from({ length: Math.ceil(message_count / 1000) }, (_, i) => i + 1);
        }
        
        console.log(`Loading chat from folder: ${folderPath}, message count: ${message_count}, result IDs: ${resultIds}`);
            
        const data = await loadJSON(`${folderPath}/result_${resultIds[0]}.json`);
        console.log(data);
        // ℹ️ Інфо про чат
        chatId.innerText = chatMeta.user_id;
        chatName.innerText = chatMeta.chat_name || "-";
        chatUsername.innerText = chatMeta.username? ("@"+chatMeta.username): "—";
        chatPhone.innerText = chatMeta.phone || "-";
        chatSize.innerText = chatMeta.message_count;
        chatType.innerText = chatMeta.chat_type;
        chatDate.innerText = chatMeta.last_activity.replace("T", " ") || "-";
        chatPhotos.innerText = chatMeta.photos || 0;
        chatDocuments.innerText = chatMeta.documents || 0;
        chatVideos.innerText = chatMeta.videos || 0;
        chatAudios.innerText = chatMeta.audios || 0;
        chatAMessages.innerText = chatMeta.voice_messages || 0;
        chatVMessages.innerText = chatMeta.video_messages || 0;
        if (chatMeta.avatar) {
            chatAvatar.src = `${folderPath}/${chatMeta.avatar}`;
        } else {
            chatAvatar.src = "static/images/default-avatar.png";
        }

        // // 💬 Повідомлення
        chatMessagesSection.innerHTML = "";
        if (data){
            data.messages.forEach(msg  => {
                const div = document.createElement("div");
                div.classList.add("message");
                let isOutgoing = false;
                if (msg.from_id) {
                    isOutgoing = msg.from_id.replace("user","") == chatMeta.user_id;
                }
                div.classList.add(isOutgoing ? "outgoing" : "incoming");
                let content = "";

                if (msg.text && msg.text !== "") {
                    content += `<div class="text">${msg.text}</div>`;
                }
                if (msg.photo) {
                    content += `<img src="${folderPath}/${msg.photo}" class="chat-media" style="max-width:100%; border-radius:6px; margin-top:5px;" />`;
                }

                if (msg.file && msg.mime_type?.startsWith("image/")) {
                    content += `<img src="${folderPath}/${msg.file}" class="chat-media" style="max-width:100%; border-radius:6px; margin-top:5px;" />`;
                }

                if (msg.file && msg.mime_type?.startsWith("audio/")) {
                    content += `<audio controls src="${folderPath}/${msg.file}" style="width:300px; margin-top:5px;"></audio>`;
                }

                if (msg.file && msg.mime_type?.startsWith("video/")) {
                    content += `<video controls src="${folderPath}/${msg.file}" style="max-width:100%; border-radius:6px; margin-top:5px;"></video>`;
                }

                if (msg.file && !msg.mime_type?.startsWith("image/") && !msg.mime_type?.startsWith("video/") && !msg.mime_type?.startsWith("audio/")) {
                    const fileName = msg.file.split("/").pop();
                    content += `<a href="${folderPath}/${msg.file}" download style="display:block; margin-top:5px;">📄 ${fileName}</a>`;
                }

                content += `<span class="timestamp">${msg.date}</span>`;
                div.innerHTML = content;
                chatMessagesSection.appendChild(div);
            });
        }
       
    }

    // 👁 Кнопка для показу/приховання контактів
    // const contactToggle = document.getElementById("contact-toggle");
    // contactToggle.addEventListener("click", () => {
    //     contactSection.classList.toggle("hidden");
    //     contactToggle.innerText = contactSection.classList.contains("hidden") ? "👁" : "🙈";
    // });
});

function isLetter(char) {
  if (char === '?') return char;
  return /^[a-zA-Zа-яА-ЯїЇєЄіІґҐ0-9]$/.test(char);
}
function randInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}