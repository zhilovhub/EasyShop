<template>
  <FilterComponent @close="filterComponentIsActive = false" v-if="filterComponentIsActive"/>
  <div v-else>
    <div v-if="items.length === 0 && isLoading === false"
         style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -75%); text-align: center; width: 350px"
    >
      <div style="font-size: 24px; font-weight: 600; word-wrap: break-word; margin-bottom: 20px">Товары в магазине отсутствуют</div>
      <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g clip-path="url(#clip0_349_452)">
          <path d="M36 72C28.8799 72 21.9197 69.8887 15.9995 65.9329C10.0793 61.9772 5.46511 56.3548 2.74035 49.7766C0.0155983 43.1985 -0.697322 35.9601 0.691746 28.9768C2.08081 21.9935 5.50948 15.5789 10.5442 10.5442C15.5789 5.50948 21.9935 2.08081 28.9768 0.691746C35.9601 -0.697322 43.1985 0.0155983 49.7766 2.74035C56.3548 5.46511 61.9772 10.0793 65.9329 15.9995C69.8887 21.9197 72 28.8799 72 36C71.9897 45.5446 68.1935 54.6954 61.4445 61.4445C54.6954 68.1935 45.5446 71.9897 36 72ZM36 6.00002C30.0666 6.00002 24.2664 7.75949 19.3329 11.0559C14.3994 14.3524 10.5543 19.0377 8.28363 24.5195C6.013 30.0013 5.4189 36.0333 6.57646 41.8527C7.73402 47.6722 10.5912 53.0177 14.7868 57.2132C18.9824 61.4088 24.3279 64.266 30.1473 65.4236C35.9667 66.5811 41.9987 65.987 47.4805 63.7164C52.9623 61.4458 57.6477 57.6006 60.9441 52.6671C64.2405 47.7337 66 41.9335 66 36C65.9913 28.0462 62.8278 20.4207 57.2036 14.7965C51.5794 9.17226 43.9538 6.00875 36 6.00002ZM53.238 53.001C53.5009 52.7071 53.7032 52.3642 53.8334 51.9919C53.9636 51.6197 54.0192 51.2255 53.9969 50.8318C53.9746 50.4381 53.8749 50.0526 53.7035 49.6975C53.5321 49.3423 53.2924 49.0244 52.998 48.762C48.2344 44.6924 42.2574 42.3147 36 42C29.7427 42.3147 23.7656 44.6924 19.002 48.762C18.4077 49.2911 18.0478 50.0347 18.0017 50.8291C17.9556 51.6235 18.2269 52.4037 18.756 52.998C19.2851 53.5924 20.0287 53.9522 20.8231 53.9983C21.6175 54.0445 22.3977 53.7731 22.992 53.244C26.6594 50.1562 31.2164 48.3191 36 48C40.7835 48.3195 45.3404 50.1566 49.008 53.244C49.6016 53.7717 50.3803 54.0425 51.1733 53.9969C51.9662 53.9514 52.7087 53.5932 53.238 53.001ZM18 30C18 33 20.685 33 24 33C27.315 33 30 33 30 30C30 28.4087 29.3679 26.8826 28.2427 25.7574C27.1174 24.6322 25.5913 24 24 24C22.4087 24 20.8826 24.6322 19.7574 25.7574C18.6322 26.8826 18 28.4087 18 30ZM42 30C42 33 44.685 33 48 33C51.315 33 54 33 54 30C54 28.4087 53.3679 26.8826 52.2427 25.7574C51.1174 24.6322 49.5913 24 48 24C46.4087 24 44.8826 24.6322 43.7574 25.7574C42.6322 26.8826 42 28.4087 42 30Z" fill="#71CBFF"/>
        </g>
        <defs>
          <clipPath id="clip0_349_452">
            <rect width="72" height="72" fill="white"/>
          </clipPath>
        </defs>
      </svg>
    </div>
    <div v-else class="wrapper">
      <div v-if="this.inputIsActive" class="header">
      <span>Поиск по товарам</span>
      <svg @click="this.inputIsActive = false" width="13" height="13" viewBox="0 0 13 13" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g clip-path="url(#clip0_1099_14080)">
          <path d="M7.64881 6.50047L12.7619 1.3879C13.0793 1.0705 13.0793 0.555904 12.7619 0.238535C12.4445 -0.0788605 11.9299 -0.0788605 11.6126 0.238535L6.49998 5.35164L1.38741 0.238535C1.07001 -0.0788605 0.555416 -0.0788605 0.238046 0.238535C-0.0793234 0.55593 -0.0793488 1.07053 0.238046 1.3879L5.35115 6.50047L0.238046 11.6131C-0.0793488 11.9305 -0.0793488 12.4451 0.238046 12.7624C0.555442 13.0798 1.07004 13.0798 1.38741 12.7624L6.49998 7.6493L11.6126 12.7624C11.9299 13.0798 12.4445 13.0798 12.7619 12.7624C13.0793 12.445 13.0793 11.9304 12.7619 11.6131L7.64881 6.50047Z" fill="currentColor"/>
        </g>
        <defs>
          <clipPath id="clip0_1099_14080">
            <rect width="13" height="13" fill="white"/>
          </clipPath>
        </defs>
      </svg>
    </div>
      <div v-else class="header">
      <span>Управление товарами</span>
      <div class="images">
        <svg @click="filterComponentIsActive = !filterComponentIsActive" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <g clip-path="url(#clip0_1019_10893)">
          <path d="M0.833333 3.95806H3.11333C3.2922 4.61617 3.68264 5.19714 4.22444 5.61134C4.76623 6.02553 5.42927 6.24994 6.11125 6.24994C6.79323 6.24994 7.45627 6.02553 7.99806 5.61134C8.53986 5.19714 8.9303 4.61617 9.10917 3.95806H19.1667C19.3877 3.95806 19.5996 3.87026 19.7559 3.71398C19.9122 3.5577 20 3.34574 20 3.12473C20 2.90371 19.9122 2.69175 19.7559 2.53547C19.5996 2.37919 19.3877 2.29139 19.1667 2.29139H9.10917C8.9303 1.63328 8.53986 1.05232 7.99806 0.638118C7.45627 0.223921 6.79323 -0.000488281 6.11125 -0.000488281C5.42927 -0.000488281 4.76623 0.223921 4.22444 0.638118C3.68264 1.05232 3.2922 1.63328 3.11333 2.29139H0.833333C0.61232 2.29139 0.400358 2.37919 0.244078 2.53547C0.0877974 2.69175 0 2.90371 0 3.12473C0 3.34574 0.0877974 3.5577 0.244078 3.71398C0.400358 3.87026 0.61232 3.95806 0.833333 3.95806ZM6.11083 1.66639C6.39926 1.66639 6.68122 1.75192 6.92104 1.91217C7.16086 2.07241 7.34778 2.30017 7.45816 2.56665C7.56854 2.83312 7.59742 3.12635 7.54115 3.40923C7.48488 3.69212 7.34598 3.95197 7.14203 4.15592C6.93808 4.35988 6.67823 4.49877 6.39534 4.55504C6.11245 4.61131 5.81923 4.58243 5.55275 4.47205C5.28628 4.36167 5.05852 4.17476 4.89827 3.93493C4.73803 3.69511 4.6525 3.41316 4.6525 3.12473C4.65294 2.73809 4.80673 2.36741 5.08012 2.09402C5.35352 1.82062 5.72419 1.66684 6.11083 1.66639Z" fill="currentColor"/>
          <path d="M19.1667 9.16672H16.8867C16.7081 8.50846 16.3178 7.92728 15.7761 7.51291C15.2343 7.09854 14.5712 6.87402 13.8892 6.87402C13.2071 6.87402 12.544 7.09854 12.0023 7.51291C11.4605 7.92728 11.0702 8.50846 10.8917 9.16672H0.833333C0.61232 9.16672 0.400358 9.25452 0.244078 9.4108C0.0877974 9.56708 0 9.77904 0 10.0001C0 10.2211 0.0877974 10.433 0.244078 10.5893C0.400358 10.7456 0.61232 10.8334 0.833333 10.8334H10.8917C11.0702 11.4916 11.4605 12.0728 12.0023 12.4872C12.544 12.9016 13.2071 13.1261 13.8892 13.1261C14.5712 13.1261 15.2343 12.9016 15.7761 12.4872C16.3178 12.0728 16.7081 11.4916 16.8867 10.8334H19.1667C19.3877 10.8334 19.5996 10.7456 19.7559 10.5893C19.9122 10.433 20 10.2211 20 10.0001C20 9.77904 19.9122 9.56708 19.7559 9.4108C19.5996 9.25452 19.3877 9.16672 19.1667 9.16672ZM13.8892 11.4584C13.6007 11.4584 13.3188 11.3729 13.079 11.2126C12.8391 11.0524 12.6522 10.8246 12.5418 10.5581C12.4315 10.2917 12.4026 9.99843 12.4589 9.71555C12.5151 9.43266 12.654 9.17281 12.858 8.96885C13.0619 8.7649 13.3218 8.62601 13.6047 8.56974C13.8875 8.51347 14.1808 8.54235 14.4472 8.65273C14.7137 8.76311 14.9415 8.95002 15.1017 9.18985C15.262 9.42967 15.3475 9.71162 15.3475 10.0001C15.3471 10.3867 15.1933 10.7574 14.9199 11.0308C14.6465 11.3042 14.2758 11.4579 13.8892 11.4584Z" fill="currentColor"/>
          <path d="M19.1667 16.0416H9.10917C8.9303 15.3835 8.53986 14.8026 7.99806 14.3884C7.45627 13.9742 6.79323 13.7498 6.11125 13.7498C5.42927 13.7498 4.76623 13.9742 4.22444 14.3884C3.68264 14.8026 3.2922 15.3835 3.11333 16.0416H0.833333C0.61232 16.0416 0.400358 16.1294 0.244078 16.2857C0.0877974 16.442 0 16.654 0 16.875C0 17.096 0.0877974 17.3079 0.244078 17.4642C0.400358 17.6205 0.61232 17.7083 0.833333 17.7083H3.11333C3.2922 18.3664 3.68264 18.9474 4.22444 19.3616C4.76623 19.7758 5.42927 20.0002 6.11125 20.0002C6.79323 20.0002 7.45627 19.7758 7.99806 19.3616C8.53986 18.9474 8.9303 18.3664 9.10917 17.7083H19.1667C19.3877 17.7083 19.5996 17.6205 19.7559 17.4642C19.9122 17.3079 20 17.096 20 16.875C20 16.654 19.9122 16.442 19.7559 16.2857C19.5996 16.1294 19.3877 16.0416 19.1667 16.0416ZM6.11083 18.3333C5.8224 18.3333 5.54045 18.2478 5.30063 18.0875C5.0608 17.9273 4.87389 17.6995 4.76351 17.4331C4.65313 17.1666 4.62425 16.8734 4.68052 16.5905C4.73679 16.3076 4.87568 16.0477 5.07964 15.8438C5.28359 15.6398 5.54344 15.5009 5.82633 15.4447C6.10922 15.3884 6.40244 15.4173 6.66891 15.5276C6.93539 15.638 7.16315 15.8249 7.32339 16.0648C7.48364 16.3046 7.56917 16.5865 7.56917 16.875C7.56851 17.2615 7.41465 17.6321 7.1413 17.9054C6.86795 18.1788 6.4974 18.3326 6.11083 18.3333Z" fill="currentColor"/>
        </g>
        <defs>
          <clipPath id="clip0_1019_10893">
            <rect width="20" height="20" fill="white"/>
          </clipPath>
        </defs>
      </svg>
        <svg @click="toggleInput" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <g clip-path="url(#clip0_1019_10954)">
            <path d="M19.9998 18.8217L14.7815 13.6034C16.137 11.9456 16.8035 9.83014 16.643 7.6947C16.4826 5.55925 15.5075 3.56717 13.9195 2.1305C12.3314 0.693821 10.252 -0.0775273 8.11119 -0.0240008C5.97039 0.0295257 3.93207 0.903832 2.41783 2.41807C0.903588 3.93231 0.0292815 5.97064 -0.024245 8.11143C-0.0777715 10.2522 0.693577 12.3317 2.13025 13.9197C3.56693 15.5077 5.55901 16.4828 7.69445 16.6433C9.82989 16.8037 11.9453 16.1372 13.6032 14.7817L18.8215 20.0001L19.9998 18.8217ZM8.33315 15.0001C7.01461 15.0001 5.72568 14.6091 4.62935 13.8765C3.53302 13.144 2.67854 12.1028 2.17395 10.8846C1.66937 9.66644 1.53735 8.326 1.79458 7.03279C2.05182 5.73959 2.68676 4.5517 3.61911 3.61935C4.55146 2.687 5.73934 2.05206 7.03255 1.79483C8.32576 1.53759 9.6662 1.66961 10.8844 2.1742C12.1025 2.67878 13.1437 3.53327 13.8763 4.62959C14.6088 5.72592 14.9998 7.01485 14.9998 8.3334C14.9978 10.1009 14.2948 11.7954 13.045 13.0452C11.7952 14.2951 10.1007 14.9981 8.33315 15.0001Z" fill="currentColor"/>
          </g>
          <defs>
            <clipPath id="clip0_1019_10954">
              <rect width="20" height="20" fill="currentColor"/>
            </clipPath>
          </defs>
        </svg>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M10.936 9.15989L10.9365 1.25613C10.9365 0.76548 10.5387 0.367733 10.0481 0.367753C9.55744 0.367753 9.15969 0.7655 9.15971 1.25613L9.1601 9.15989L1.25636 9.15948C0.765714 9.15948 0.367967 9.55722 0.367987 10.0479C0.368006 10.5385 0.765734 10.9362 1.25636 10.9362L9.1601 10.9358L9.15971 18.8396C9.15971 19.3302 9.55746 19.728 10.0481 19.728C10.5387 19.7279 10.9365 19.3302 10.9365 18.8396L10.936 10.9358L18.8398 10.9362C19.3304 10.9362 19.7282 10.5385 19.7282 10.0479C19.7282 9.55722 19.3304 9.15947 18.8398 9.1595L10.936 9.15989Z" fill="currentColor"/>
      </svg>
      </div>
    </div>
      <div v-if="isLoading" class="loading-message">
        Загрузка...
      </div>
      <div v-else>
        <div class="input-block" v-if="inputIsActive">
      <input autofocus @focusout="toggleInput" v-model="inputValue" placeholder="Введите название или ID">
    </div>
        <div v-else class="block-template">
          <img @click="toggleMainCircle" v-if="!mainCircleIsActive" src="@/assets/circle.png" alt="circle png">
          <img @click="toggleMainCircle" v-else src="@/assets/markedcircle.png" alt="marked circle png">
          <span>Название товара</span>
          <span class="span-id">ID</span>
        <span style="text-align: center">Кол-во на <br> складе</span>
        <svg :class="this.itemsForDelete.length > 0 ? 'binIsActive' : 'bin'" @click="toggleModelWindow" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <g clip-path="url(#clip0_1090_10882)">
            <path d="M17.5003 3.33333H14.917C14.7236 2.39284 14.2118 1.54779 13.468 0.940598C12.7242 0.333408 11.7938 0.0012121 10.8337 0L9.16699 0C8.20682 0.0012121 7.27642 0.333408 6.53262 0.940598C5.78881 1.54779 5.27707 2.39284 5.08366 3.33333H2.50033C2.27931 3.33333 2.06735 3.42113 1.91107 3.57741C1.75479 3.73369 1.66699 3.94565 1.66699 4.16667C1.66699 4.38768 1.75479 4.59964 1.91107 4.75592C2.06735 4.9122 2.27931 5 2.50033 5H3.33366V15.8333C3.33498 16.938 3.77439 17.997 4.55551 18.7782C5.33662 19.5593 6.39566 19.9987 7.50033 20H12.5003C13.605 19.9987 14.664 19.5593 15.4451 18.7782C16.2263 17.997 16.6657 16.938 16.667 15.8333V5H17.5003C17.7213 5 17.9333 4.9122 18.0896 4.75592C18.2459 4.59964 18.3337 4.38768 18.3337 4.16667C18.3337 3.94565 18.2459 3.73369 18.0896 3.57741C17.9333 3.42113 17.7213 3.33333 17.5003 3.33333V3.33333ZM9.16699 1.66667H10.8337C11.3506 1.6673 11.8546 1.82781 12.2767 2.1262C12.6987 2.42459 13.0182 2.84624 13.1912 3.33333H6.80949C6.98248 2.84624 7.30191 2.42459 7.72398 2.1262C8.14605 1.82781 8.6501 1.6673 9.16699 1.66667V1.66667ZM15.0003 15.8333C15.0003 16.4964 14.7369 17.1323 14.2681 17.6011C13.7993 18.0699 13.1634 18.3333 12.5003 18.3333H7.50033C6.83728 18.3333 6.2014 18.0699 5.73256 17.6011C5.26372 17.1323 5.00033 16.4964 5.00033 15.8333V5H15.0003V15.8333Z" fill="currentColor"/>
            <path d="M8.33333 14.9997C8.55434 14.9997 8.76631 14.9119 8.92259 14.7556C9.07887 14.5993 9.16666 14.3873 9.16666 14.1663V9.16634C9.16666 8.94533 9.07887 8.73337 8.92259 8.57709C8.76631 8.42081 8.55434 8.33301 8.33333 8.33301C8.11232 8.33301 7.90036 8.42081 7.74408 8.57709C7.5878 8.73337 7.5 8.94533 7.5 9.16634V14.1663C7.5 14.3873 7.5878 14.5993 7.74408 14.7556C7.90036 14.9119 8.11232 14.9997 8.33333 14.9997Z" fill="currentColor"/>
            <path d="M11.6663 14.9997C11.8874 14.9997 12.0993 14.9119 12.2556 14.7556C12.4119 14.5993 12.4997 14.3873 12.4997 14.1663V9.16634C12.4997 8.94533 12.4119 8.73337 12.2556 8.57709C12.0993 8.42081 11.8874 8.33301 11.6663 8.33301C11.4453 8.33301 11.2334 8.42081 11.0771 8.57709C10.9208 8.73337 10.833 8.94533 10.833 9.16634V14.1663C10.833 14.3873 10.9208 14.5993 11.0771 14.7556C11.2334 14.9119 11.4453 14.9997 11.6663 14.9997Z" fill="currentColor"/>
          </g>
        <defs>
          <clipPath id="clip0_1090_10882">
            <rect width="20" height="20" fill="currentColor"/>
          </clipPath>
        </defs>
      </svg>
    </div>
        <ul class="items-styles">
    <li style="list-style-type: none" v-for="item in items">
      <div @click="toggleFooter(item, $event)" class="item-block" :style="{ borderRadius: !item.isActive ? '15px' : '15px 15px 0 0'}">
        <img @click="toggleSelected(item)" @click.stop="toggleFooter(item)" v-if="item.isSelected" src="@/assets/markedcircle.png" alt="marked circle png">
        <img @click="toggleSelected(item)" @click.stop="toggleFooter(item)" v-else src="@/assets/circle.png" alt="circle png">
        <div class="item-name">{{shortenName(item.name)}}</div>
        <span class="span-id">{{item.id}}</span>
        <span>52</span>
        <svg v-if="item.isActive" width="19" height="9" viewBox="0 0 19 9" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M-0.000309349 8.19291C-0.000910159 8.08872 0.0190579 7.98544 0.0584561 7.88898C0.0978524 7.79253 0.155903 7.7048 0.229276 7.63082L6.69719 1.16291C7.06489 0.794283 7.50169 0.501819 7.98259 0.302268C8.46349 0.102717 8.97903 -4.38158e-07 9.49969 -4.154e-07C10.0203 -3.92641e-07 10.5359 0.102717 11.0168 0.302268C11.4977 0.501819 11.9345 0.794283 12.3022 1.16291L18.7701 7.63083C18.8439 7.70464 18.9025 7.79227 18.9424 7.88871C18.9824 7.98516 19.0029 8.08852 19.0029 8.19291C19.0029 8.2973 18.9824 8.40066 18.9424 8.49711C18.9025 8.59355 18.8439 8.68118 18.7701 8.75499C18.6963 8.82881 18.6087 8.88736 18.5122 8.92731C18.4158 8.96725 18.3124 8.98781 18.208 8.98781C18.1036 8.98781 18.0003 8.96725 17.9038 8.92731C17.8074 8.88736 17.7198 8.82881 17.6459 8.75499L11.178 2.28708C10.7327 1.84232 10.1291 1.5925 9.49969 1.5925C8.87031 1.5925 8.26667 1.84232 7.82136 2.28708L1.35344 8.75499C1.27984 8.82919 1.19229 8.88809 1.09582 8.92828C0.999343 8.96847 0.895868 8.98917 0.791359 8.98917C0.686849 8.98917 0.583374 8.96847 0.486902 8.92828C0.39043 8.88809 0.302871 8.82919 0.229276 8.75499C0.155902 8.68102 0.0978523 8.59329 0.058456 8.49683C0.0190579 8.40038 -0.000910168 8.2971 -0.000309349 8.19291Z" fill="currentColor"/>
        </svg>
        <svg v-else width="19" height="9" viewBox="0 0 19 9" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M19.0032 0.796349C19.0038 0.900537 18.9839 1.00382 18.9445 1.10028C18.9051 1.19673 18.847 1.28446 18.7737 1.35843L12.3057 7.82635C11.938 8.19497 11.5012 8.48744 11.0203 8.68699C10.5394 8.88654 10.0239 8.98926 9.50324 8.98926C8.98258 8.98926 8.46704 8.88654 7.98614 8.68699C7.50524 8.48744 7.06843 8.19497 6.70074 7.82635L0.232823 1.35843C0.159009 1.28462 0.100456 1.19699 0.0605087 1.10055C0.0205609 1.0041 9.72324e-08 0.900737 9.76995e-08 0.796349C9.81665e-08 0.691959 0.0205609 0.588593 0.0605087 0.492151C0.100456 0.395709 0.159009 0.30808 0.232823 0.234265C0.306636 0.160452 0.394266 0.101898 0.490709 0.0619507C0.587151 0.0220032 0.690517 0.00144292 0.794906 0.00144292C0.899294 0.00144292 1.00266 0.0220032 1.0991 0.0619507C1.19555 0.101898 1.28318 0.160452 1.35699 0.234265L7.82491 6.70218C8.27022 7.14694 8.87386 7.39676 9.50324 7.39676C10.1326 7.39676 10.7363 7.14694 11.1816 6.70218L17.6495 0.234266C17.7231 0.160064 17.8106 0.101168 17.9071 0.0609753C18.0036 0.0207836 18.1071 9.17687e-05 18.2116 9.17699e-05C18.3161 9.17712e-05 18.4196 0.0207836 18.516 0.0609753C18.6125 0.101168 18.7001 0.160064 18.7737 0.234266C18.847 0.308239 18.9051 0.395968 18.9445 0.492422C18.9839 0.588877 19.0038 0.69216 19.0032 0.796349Z" fill="currentColor"/>
        </svg>
      </div>

      <div class="block-footer" v-if="item.isActive">
        <hr>
        <div>
          <span>Категория <br>товара</span>
          <span>{{item.category[0]}}</span>
        </div>
        <hr>
        <div>
          <span>Цена</span>
          <span>{{item.price}}₽</span>
        </div>
      </div>
    </li>
  </ul>
        <div v-if="deleteModelWindowIsActive" class="model-wrapper">
      <div class="model-window">
        <svg @click="deleteModelWindowIsActive = !deleteModelWindowIsActive" width="13" height="13" viewBox="0 0 13 13" fill="none" xmlns="http://www.w3.org/2000/svg">
          <g clip-path="url(#clip0_1099_14080)">
            <path d="M7.64881 6.50047L12.7619 1.3879C13.0793 1.0705 13.0793 0.555904 12.7619 0.238535C12.4445 -0.0788605 11.9299 -0.0788605 11.6126 0.238535L6.49998 5.35164L1.38741 0.238535C1.07001 -0.0788605 0.555416 -0.0788605 0.238046 0.238535C-0.0793234 0.55593 -0.0793488 1.07053 0.238046 1.3879L5.35115 6.50047L0.238046 11.6131C-0.0793488 11.9305 -0.0793488 12.4451 0.238046 12.7624C0.555442 13.0798 1.07004 13.0798 1.38741 12.7624L6.49998 7.6493L11.6126 12.7624C11.9299 13.0798 12.4445 13.0798 12.7619 12.7624C13.0793 12.445 13.0793 11.9304 12.7619 11.6131L7.64881 6.50047Z" fill="currentColor"/>
          </g>
          <defs>
            <clipPath id="clip0_1099_14080">
              <rect width="13" height="13" fill="white"/>
            </clipPath>
          </defs>
        </svg>
        <div class="warning-span">Вы уверены, что хотите удалить товар/ы?</div>
        <div class="block-items">
          <div class="item-for-delete" v-for="item in itemsForDelete">
            <div>Название: {{shortenNameForModelWindow(item.name)}} <br>
              ID: {{item.price}}</div>
            <hr>
          </div>
        </div>
        <div class="button-block">
          <button>Удалить</button>
          <button @click="deleteModelWindowIsActive = !deleteModelWindowIsActive">Отмена</button>
        </div>
      </div>
    </div>
      </div>
    </div>
  </div>
</template>

<script>
import FilterComponent from '@/components/products/filterComponent.vue'
import { mapState } from 'vuex'
import { tg } from '@/main.js'

export default {
  data() {
    return {
      isLoading: true,
      filterComponentIsActive: false,
      mainCircleIsActive: false,
      deleteModelWindowIsActive: false,
      inputIsActive: false,
      inputValue: ''
    }
  },
  components: { FilterComponent },
  mounted() {
    this.$store.dispatch('itemsInit').then(() =>{
      this.isLoading = false;
    });
    tg.onEvent('backButtonClicked', this.toggleInput);
  },
  computed: {
    ...mapState({
      items: state => state.items,
    }),
    itemsForDelete() {
      return this.$store.state.items.filter(item => item.isSelected === true);
    }
  },
  methods: {
    shortenName(name) {
      if (!name) return '';
      return name.length > 18 ? name.substring(0, 12) + '...' : name;
    },
    shortenNameForModelWindow(name) {
      if (!name) return '';
      return name.length > 25 ? name.substring(0, 22) + '...' : name;
    },
    toggleSelected(item) {
      item.isSelected = !item.isSelected;
      console.log(this.itemsForDelete);
    },
    toggleFooter(item, event) {
      try {
        if (event.target) {
          item.isActive = !item.isActive;
        }
      } catch (error) {
        return error
      }
    },
    toggleMainCircle() {
      this.mainCircleIsActive = !this.mainCircleIsActive;
      if (this.mainCircleIsActive) {
        this.$store.state.items = this.$store.state.items.map(item => ({...item, isSelected: true}));
      } else {
        this.$store.state.items = this.$store.state.items.map(item => ({...item, isSelected: false}));
      }
    },
    toggleModelWindow() {
      if (this.itemsForDelete.length > 0) {
        this.deleteModelWindowIsActive = !this.deleteModelWindowIsActive
      }
    },
    toggleInput() {
      this.inputValue = ''
      this.inputIsActive = true;

      tg.onEvent('backButtonClicked', this.closeSearching);

      tg.BackButton.show();
    },
    closeSearching() {
      tg.BackButton.hide();

      this.inputIsActive = false;
      tg.offEvent('backButtonClicked', this);
    },
  }
}
</script>

<style scoped lang="scss">
*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  font-size: 15px;
  line-height: 18.29px;
}

span, div, button {
  color: var(--app-text-color);
}

svg {
  color: var(--app-text-color);
}

.header {
  max-width: 100%;
  margin: 0 5%;
  padding-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  .images {
    display: flex;
    svg {
      margin: 0 5px;
      width: 20px;
      height: 20px;
    }
  }
  span {
    font-size: 20px;
    font-weight: bold;
  }
}

.block-template {
  margin: 0 5%;
  padding-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  img {
    width: 20px;
    height: 20px;
    margin: 0 10px;
  }
  svg {
    margin: 0 5px;
    width: 20px;
    height: 20px;
  }
  span {
    font-size: 12px;
    font-weight: 400;
  }
}

.span-id {
  padding: 5px 10px;
  border-left: 2px solid var(--app-hr-border-color);
  border-right: 2px solid var(--app-hr-border-color);
}

.items-styles{
  width: 90%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100%, 1fr));
  grid-column: 1;
  grid-gap: 10px;
  padding: 0;
  margin: 20px auto 50px;
  .item-block{
    height: 54px;
    white-space: nowrap;
    background-color: var(--app-card-background-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 15px 15px 0 0;
    font-size: 14px;
    .item-name {
      font-weight: bold;
      width: 80px;
      white-space: break-spaces;
      text-align: center;
    }
    img {
      width: 20px;
      height: 20px;
      margin-left: 10px;
    }
    svg {
      margin: 0 10px;
      width: 20px;
      height: 20px;
    }
  }
  .block-footer {
    height: 108px;
    border-radius: 0 0 15px 15px;
    background-color: var(--app-card-background-color);
    div {
      display: flex;
      justify-content: start;
      align-items: center;
      padding: 10px 10px;
      span {
        font-weight: 550;
        text-align: center;
      }
      span:first-child {
        text-align: start;
        font-weight: 350;
        margin-right: 10px;
        width: 100px;
      }
    }
  }
}

hr {
  border: 1px solid var(--app-hr-border-color);
  width: 97.5%;
  margin: 0 auto;
}

.model-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgb(0, 0, 0, 30%);
  .model-window {
    background-color: var(--app-card-background-color);
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -75%);
    width: 90%;
    padding: 20px 5%;
    border-radius: 15px;
    .warning-span {
      width: 100%;
      font-size: 20px;
      line-height: 24px;
      text-align: center;
      font-weight: bolder;
      margin: 10px 0;
    }
    svg {
      position: absolute;
      right: 5%;
    }
    .block-items {
      .item-for-delete {
        padding: 5px 0;
        div {
          line-height: 24px;
          padding: 5px 0;
        }
      }
    }
    .block-items > :last-child {
      hr:last-child {
        opacity: 0;
      }
    }
    .button-block {
      display: flex;
      justify-content: space-around;
      width: 100%;
      margin: 5px 0 0;
      button {
        width: 47.5%;
        height: 37px;
        border-radius: 15px;
        font-weight: 600;
      }
      button:first-child {
        background-color: var(--app-button-delete-bg);
        box-shadow: 0 1px 2px 0 rgb(0, 0, 0, 25%);
        border: none;
      }
      button:last-child {
        background-color: var(--app-button-bgcolor);
        border: none;
        box-shadow: 0 1px 2px 0 rgb(0, 0, 0, 25%);
      }
    }
  }
}

.input-block {
  margin: 20px 5%;
  input {
    width: 100%;
    padding: 10px 20px;
    border-radius: 15px;
    color: var(--app-text-color);
    background: var(--app-card-background-color) url("@/assets/search.svg") no-repeat center right 3vw;
    border: none;
    &:focus {
      outline: 2px solid var(--app-text-color);
      &::placeholder {
        opacity: 0;
      }
    }
  }
}

.binIsActive {
  color: red;
  fill: red;
  transition: fill 0.3s ease;
}

.bin {
  color: var(--app-text-color);
  fill: var(--app-text-color);
  opacity: 0.4;
  transition: fill 0.3s ease;
}

.loading-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  font-size: 24px;
}
</style>
