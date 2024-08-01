<script>
import { Swiper, SwiperSlide } from '@SwiperVue'
import { Navigation, Scrollbar } from '@Swiper'
import { tg } from '@/main.js'

export default {
  computed: {
    tg () {
      return tg
    },
  },
  components: { SwiperSlide, Swiper },
  props: {
    itemEditData: {
      type: Object,
    }
  },
  data() {
    return {
      productName: '',
      productDescription: '',
      productArticle: '',
      productPrice: null,
      productCount: 0,
      imagePreviews: [],
      imageFiles: [],
      options: [],
      formData: new FormData,
      categories: this.$store.state.categories,
      chosenOption: {
        bot_id: this.$store.state.bot_id,
        name: this.permChosenOption,
        id: this.permChosenOption
      },
      chosenCategory: null,
      categoryIsOpen: false,
      modelWindowOptionIsActive: false,
      modelAddingCategoryIsActive: false,
      selectingCategoryIsActive: false,
      permChosenOption: '',
      permCategoryInput: '',
      isLoading: false,
      reasonLoading: '',
      isMounted: false,
    };
  },
  unmounted() {
    tg.offEvent('mainButtonClicked', this.addProduct);
    tg.offEvent('mainButtonClicked', this.editProduct);
    tg.offEvent('backButtonClicked', this.closingComponent);
  },
  mounted() {
    if (this.itemEditData && this.itemEditData.id) {
      this.productName = this.itemEditData.name;
      this.productDescription = this.itemEditData.description;
      this.productArticle = this.itemEditData.article;
      this.productPrice = this.itemEditData.price;
      this.productCount = this.itemEditData.count;
      this.options = this.itemEditData.extra_options || [];


      this.imageFiles = [];
      this.imagePreviews = [];

      let vm = this;

      this.isLoading = true;
      this.reasonLoading = "Загрузка фотографий товара...";
      try {
        if (this.itemEditData.picture) {
          this.itemEditData.picture.forEach(item => {
            if (item) {
              let api_url = this.$store.state.api_url + "/files/get_file/" + item;
              this.imagePreviews.push(item);

              console.log(api_url)

              fetch(api_url)
                .then(res => {
                  console.log(res);
                  return res.blob();
                })
                .then(blob => {
                  console.log(blob);
                  vm.imageFiles.push(blob);
                });
            }
          })
        }
        this.isLoading = false;
      } catch (err) {
        this.reasonLoading = "Произошла ошибка при загрузке фотографий. " + err
      }

      if (!this.imagePreviews) {
        this.imagePreviews = [];
      }
      if (!this.imageFiles) {
        this.imageFiles = [];
      }

      console.log("this.imageFiles", this.imageFiles)
      console.log("this.imagePreviews", this.imagePreviews)

      tg.MainButton.show();
      tg.BackButton.show();
      tg.MainButton.text = "Изменить товар";
      tg.MainButton.textColor = "#0C0C0C";
      tg.onEvent('mainButtonClicked', this.editProduct);
    } else {
      tg.MainButton.show();
      tg.BackButton.show();
      tg.MainButton.text = "Добавить товар";
      tg.MainButton.textColor = "#0C0C0C";
      tg.onEvent('mainButtonClicked', this.addProduct);
    }

    tg.onEvent('backButtonClicked', this.closingComponent);

    setTimeout(() => {
      this.isMounted = true;
    }, 50);

    this.$nextTick(this.setFirstOptionChosen);
    this.$store.dispatch('getCategories').then(() => {
      this.categories = this.$store.state.categories;
      if (this.itemEditData) {
        this.initChooseCategory(this.itemEditData);
        this.handleFileUpload(null);
      }
    });
  },
  setup() {
    return {
      modules: [Scrollbar, Navigation],
    };
  },
  methods: {
    addProduct() {
      if (this.productName && this.productArticle && this.productPrice && this.productCount && this.chosenCategory) {
        this.$store.dispatch("addProduct", {
          name: this.productName,
          category: [this.chosenCategory],
          description: this.productDescription,
          article: this.productArticle,
          price: this.productPrice,
          count: this.productCount,
          extra_options: this.options,
          images: this.imageFiles
        }).then((response) => {
          if (response === 409) {
            const articleInput = document.getElementById('articleInput');
            articleInput.style.border = '1px solid #ff003c';
            articleInput.value = ''
            articleInput.placeholder = 'Артикул был занят';
            articleInput.classList.add('red-placeholder');
            return
          }
          this.isMounted = false;
          setTimeout(() => {
            tg.MainButton.hide();
            tg.BackButton.hide();
            this.$emit("close");
          }, 100);
        });

      } else {
        const requiredItems = document.querySelectorAll('.required');
        console.log(requiredItems);
        if (!this.chosenCategory) {
          requiredItems[0].style.border = '1px solid #ff003c';
          requiredItems[0].placeholder = 'Поле не может быть пустым';
          requiredItems[0].classList.add('red-placeholder');
        }
        if (!this.productPrice) {
          requiredItems[4].style.border = '1px solid #ff003c';
          requiredItems[4].placeholder = 'Поле не может быть пустым';
          requiredItems[4].classList.add('red-placeholder');
        }
        if (!this.productCount) {
          requiredItems[5].style.border = '1px solid #ff003c';
          requiredItems[5].placeholder = 'Поле не может быть пустым';
          requiredItems[5].classList.add('red-placeholder');
        }
        requiredItems.forEach(item => {
          if (item.value === '') {
            item.style.border = '1px solid #ff003c';
            item.placeholder = 'Поле не может быть пустым';
            item.classList.add('red-placeholder');
          }
        })
      }
    },
    editProduct() {
      console.log("editProduct", this.imageFiles)
      this.$store.dispatch("editProduct", {
        name: this.productName,
        category: [this.chosenCategory],
        description: this.productDescription,
        article: this.productArticle,
        price: this.productPrice,
        count: this.productCount,
        picture: this.imageFiles,
        extra_options: this.options,
        id: this.itemEditData.id
      }).then(() => {
        tg.MainButton.hide();
        tg.BackButton.hide();
        this.$emit("close");
      }, 100);
    },
    closingComponent() {
      this.isMounted = false;
      setTimeout(() => {
        this.$emit("close");
      }, 100);
    },
    handleFileUpload(event) {
      console.log("cats", this.categories)
      console.log('CCAT', this.chosenCategory)
      if (!this.imageFiles) {
        this.imageFiles = [];
      }
      if (!this.imagePreviews) {
        this.imagePreviews = [];
      }
      if (event) {
        const newFiles = Array.from(event.target.files);
        if (this.imageFiles.length + newFiles.length > 5) {
          alert("Вы можете загрузить максимум 5 фоток.");
          return;
        }
        this.isLoading = true;
        function get_file_type(header) {
          let _type;
          console.log(header);
          let first_part = header.slice(0, 4 * 2);
          let second_part = header.slice(5, 9 * 2 + 1)
          console.log(first_part)
          console.log(second_part)
          if (first_part === "89504e47") {
            _type = "image/png";
          } else if (["ffd8ffe8", "ffd8ffe3", "ffd8ffe2", "ffd8ffe1", "ffd8ffe0"].includes(first_part)) {
            _type = "image/jpeg";
          } else if (["66747970686569", "63667479706d", "667479706d6966"].includes(second_part)) {
            _type = "image/heic";
          } else {
            _type = "unknown";
          }
          console.log("uploaded file MIME type: " + _type)

          switch (_type){
            case "image/heic":
              console.log("heic file uploaded");
              break;
            case "image/jpeg":
            case "image/png":
              break;
          }
          return _type
        }
        let vm = this;
        // let imagePreviews = this.imagePreviews;
        // let imageFiles = this.imageFiles;
        // let my_store = this.$store
        console.log("this", this.imagePreviews)
        console.log("foreach", vm.imagePreviews)

        newFiles.forEach(file => {
          console.log(file);

          let fileReader = new FileReader();

          fileReader.onloadend = (function (f) {
            return function (e) {
              vm.reasonLoading = "Загрузка файла...";
              console.log(e)
              console.log(f)
              console.log("filereader", vm.imagePreviews)
              let arr = (new Uint8Array(e.target.result));
              let header = "";

              for (var i = 0; i < arr.length; i++) {
                header += arr[i].toString(16);
              }
              vm.reasonLoading = "Распознаем тип файла...";

              let type;
              type = get_file_type(header);

              vm.reasonLoading = "Обработка полученного файла с типом " + type + " ...";

              if (type === "image/heic") {
                vm.$store.dispatch("convertHEIC", [f, vm.imagePreviews, vm.imageFiles, vm]).then((data) => {
                  let that = data[3];
                  that.reasonLoading = "Загрузка предпросмотрa обработанного файла...";
                  try {
                    if (!that.imagePreviews) {
                      that.imagePreviews = [];
                    }
                    if (!that.imageFiles) {
                      that.imageFiles = [];
                    }
                    let modified_file = data[0];
                    that.imagePreviews.push(URL.createObjectURL(modified_file));
                    that.imageFiles.push(modified_file);
                    that.isLoading = false;
                    that.reasonLoading = "";
                  } catch (err) {
                    that.reasonLoading = "Ошибка при добавлении обработанной фотографии. " + err
                  }
                });
              } else if (type === "unknown") {
                vm.isLoading = false;
                vm.reasonLoading = "";
                alert("incorrect photo type")
              } else {
                vm.reasonLoading = "Загрузка предпросмотрa файла...";
                try {
                  if (!vm.imagePreviews) {
                    vm.imagePreviews = [];
                  }
                  if (!vm.imageFiles) {
                    vm.imageFiles = [];
                  }
                  vm.imagePreviews.push(URL.createObjectURL(f))
                  vm.imageFiles.push(f)
                  vm.isLoading = false;
                  vm.reasonLoading = "";
                } catch (err) {
                  vm.reasonLoading = "Ошибка при добавлении фотографии. " + err
                }
              }
              // console.log(vm.isLoading);
            }
          })(file);

          fileReader.readAsArrayBuffer(file);

          // convertHEIC(file).then((data) => {
          //       console.log(data);
          //       let modified_file = data;
          //       this.imagePreviews.push(URL.createObjectURL(modified_file));
          //       this.imageFiles.push(modified_file);
          //     });
        });
      }
    },
    addOption() {
      if (this.permChosenOption === 'block' && this.options) {
        this.options.push({
          name: '',
          type: this.permChosenOption,
          variants: ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        })
      } else if (this.permChosenOption === 'text' && this.options) {
        this.options.push({
          name: '',
          type: this.permChosenOption,
          variants: [''],
        });
      } else {
        this.options.push({
          name: '',
          type: this.permChosenOption,
          variants: ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
          variants_prices: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        });
      }
      this.modelWindowOptionIsActive = false;
      document.body.style.overflow = '';
    },
    addCategory() {
      if (this.permCategoryInput) {
        this.$store.dispatch("addCategory", this.permCategoryInput).then(() => {
          this.$store.dispatch('getCategories').then(() => {
            this.categories = this.$store.state.categories;
          });
        });
      }
      this.modelAddingCategoryIsActive = false;
      document.body.style.overflow = '';
    },
    toggleModelWindow() {
      this.modelWindowOptionIsActive = !this.modelWindowOptionIsActive;
      if (this.modelWindowOptionIsActive) {
        document.body.style.overflow = 'hidden';
        window.scrollTo(0,0);
      } else {
        document.body.style.overflow = '';
      }
    },
    toggleModelAddingCategory() {
      this.modelAddingCategoryIsActive = !this.modelAddingCategoryIsActive;
      if (this.modelAddingCategoryIsActive) {
        document.body.style.overflow = 'hidden';
        window.scrollTo(0, 0);
      } else {
        document.body.style.overflow = '';
      }
    },
    chooseOption(target) {
      this.permChosenOption = target.id;
      const allOptions = document.querySelectorAll('.option-block');
      allOptions.forEach(option => {
        option.classList.remove('chosen');
      });
      target.closest('.option-block').classList.add('chosen');
    },
    setFirstOptionChosen() {
      let firstOption = document.querySelector('.option-block');
      if (firstOption) {
        firstOption.classList.add('chosen');
      }
      this.permChosenOption = firstOption.firstChild.id;
    },
    toggleFooter(event) {
      try {
        if (event.target) {
          this.selectingCategoryIsActive = !this.selectingCategoryIsActive;
        }
      } catch (error) {
        return error
      }
    },
    initChooseCategory(editData) {
      const allSizes = document.querySelectorAll('.category-main');
      allSizes.forEach(size => {
        size.classList.remove('chosenCategory');
      });
      this.categories.map(category => {
        if (editData.category && category.id === editData.category[0]) {
          category.isSelected = true;
          this.chosenCategory = editData.category[0];
        } else {
          category.isSelected = false;
        }
      });
      console.log("chosen cat", this.chosenCategory)
    },
    chooseCategory(item) {
      // item is category object
      const allSizes = document.querySelectorAll('.category-main');
      allSizes.forEach(size => {
        size.classList.remove('chosenCategory');
      });
      this.categories.map(category => {
        category.isSelected = category.id === item.id;
      });
      this.chosenCategory = item.id;
      console.log("new chosen cat", this.chosenCategory)
    },
  }
};
</script>

<template>
  <div class="wrapper" :style="{ opacity: isMounted ? 1 : 0 }">
    <div class="header">
      <span v-if="this.itemEditData?.id">Изменение товара</span>
      <span v-else>Добавление товара</span>
    </div>
    <div class="main">
      <div class="card">
        <h1>Категория</h1>
        <div @click="toggleFooter($event)" class="category-block required" :style="{ borderRadius: selectingCategoryIsActive ? '15px 15px 0 0' : '15px'}">
          <span>Выберите категорию</span>
          <svg v-if="selectingCategoryIsActive" width="19" height="9" viewBox="0 0 19 9" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M-0.000309349 8.19291C-0.000910159 8.08872 0.0190579 7.98544 0.0584561 7.88898C0.0978524 7.79253 0.155903 7.7048 0.229276 7.63082L6.69719 1.16291C7.06489 0.794283 7.50169 0.501819 7.98259 0.302268C8.46349 0.102717 8.97903 -4.38158e-07 9.49969 -4.154e-07C10.0203 -3.92641e-07 10.5359 0.102717 11.0168 0.302268C11.4977 0.501819 11.9345 0.794283 12.3022 1.16291L18.7701 7.63083C18.8439 7.70464 18.9025 7.79227 18.9424 7.88871C18.9824 7.98516 19.0029 8.08852 19.0029 8.19291C19.0029 8.2973 18.9824 8.40066 18.9424 8.49711C18.9025 8.59355 18.8439 8.68118 18.7701 8.75499C18.6963 8.82881 18.6087 8.88736 18.5122 8.92731C18.4158 8.96725 18.3124 8.98781 18.208 8.98781C18.1036 8.98781 18.0003 8.96725 17.9038 8.92731C17.8074 8.88736 17.7198 8.82881 17.6459 8.75499L11.178 2.28708C10.7327 1.84232 10.1291 1.5925 9.49969 1.5925C8.87031 1.5925 8.26667 1.84232 7.82136 2.28708L1.35344 8.75499C1.27984 8.82919 1.19229 8.88809 1.09582 8.92828C0.999343 8.96847 0.895868 8.98917 0.791359 8.98917C0.686849 8.98917 0.583374 8.96847 0.486902 8.92828C0.39043 8.88809 0.302871 8.82919 0.229276 8.75499C0.155902 8.68102 0.0978523 8.59329 0.058456 8.49683C0.0190579 8.40038 -0.000910168 8.2971 -0.000309349 8.19291Z" fill="currentColor"/>
          </svg>
          <svg v-else width="19" height="9" viewBox="0 0 19 9" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19.0032 0.796349C19.0038 0.900537 18.9839 1.00382 18.9445 1.10028C18.9051 1.19673 18.847 1.28446 18.7737 1.35843L12.3057 7.82635C11.938 8.19497 11.5012 8.48744 11.0203 8.68699C10.5394 8.88654 10.0239 8.98926 9.50324 8.98926C8.98258 8.98926 8.46704 8.88654 7.98614 8.68699C7.50524 8.48744 7.06843 8.19497 6.70074 7.82635L0.232823 1.35843C0.159009 1.28462 0.100456 1.19699 0.0605087 1.10055C0.0205609 1.0041 9.72324e-08 0.900737 9.76995e-08 0.796349C9.81665e-08 0.691959 0.0205609 0.588593 0.0605087 0.492151C0.100456 0.395709 0.159009 0.30808 0.232823 0.234265C0.306636 0.160452 0.394266 0.101898 0.490709 0.0619507C0.587151 0.0220032 0.690517 0.00144292 0.794906 0.00144292C0.899294 0.00144292 1.00266 0.0220032 1.0991 0.0619507C1.19555 0.101898 1.28318 0.160452 1.35699 0.234265L7.82491 6.70218C8.27022 7.14694 8.87386 7.39676 9.50324 7.39676C10.1326 7.39676 10.7363 7.14694 11.1816 6.70218L17.6495 0.234266C17.7231 0.160064 17.8106 0.101168 17.9071 0.0609753C18.0036 0.0207836 18.1071 9.17687e-05 18.2116 9.17699e-05C18.3161 9.17712e-05 18.4196 0.0207836 18.516 0.0609753C18.6125 0.101168 18.7001 0.160064 18.7737 0.234266C18.847 0.308239 18.9051 0.395968 18.9445 0.492422C18.9839 0.588877 19.0038 0.69216 19.0032 0.796349Z" fill="currentColor"/>
          </svg>
        </div>
        <Transition>
          <div class="card-footer" v-show="selectingCategoryIsActive">
            <ul class="items-styles">
              <li
                v-for="category in categories"
                class="category-item"
                @click="chooseCategory(category)"
              >
                <div class="category-main">
                  <span  :style="{ color: category.isSelected ? '#2085BE' : '' }">{{category.name}}</span>
                  <img v-if="category.isSelected" src="@/assets/markedcircle.png" alt="markedcircle">
                  <img v-else src="@/assets/circle.png" alt="circle">
                </div>
                <hr>
              </li>
            </ul>
            <div @click="toggleModelAddingCategory" style="width: 100%; display: flex; justify-content: center; margin-top: 15px">
              <svg width="25" height="25" viewBox="0 0 25 25" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12.5 0C5.60729 0 0 5.60729 0 12.5C0 19.3927 5.60729 25 12.5 25C19.3927 25 25 19.3927 25 12.5C25 5.60729 19.3927 0 12.5 0ZM12.5 23.9583C6.18229 23.9583 1.04167 18.8177 1.04167 12.5C1.04167 6.18229 6.18229 1.04167 12.5 1.04167C18.8177 1.04167 23.9583 6.18229 23.9583 12.5C23.9583 18.8177 18.8177 23.9583 12.5 23.9583ZM17.7083 12.5C17.7083 12.7875 17.475 13.0208 17.1875 13.0208H13.0208V17.1875C13.0208 17.475 12.7875 17.7083 12.5 17.7083C12.2125 17.7083 11.9792 17.475 11.9792 17.1875V13.0208H7.8125C7.525 13.0208 7.29167 12.7875 7.29167 12.5C7.29167 12.2125 7.525 11.9792 7.8125 11.9792H11.9792V7.8125C11.9792 7.525 12.2125 7.29167 12.5 7.29167C12.7875 7.29167 13.0208 7.525 13.0208 7.8125V11.9792H17.1875C17.475 11.9792 17.7083 12.2125 17.7083 12.5Z" fill="#878787"/>
              </svg>
            </div>
          </div>
        </Transition>
      </div>
      <Transition>
        <div v-show="modelAddingCategoryIsActive" class="model-wrapper">
          <div class="model-window">
            <svg @click="toggleModelAddingCategory" width="13" height="13" viewBox="0 0 13 13" fill="none" xmlns="http://www.w3.org/2000/svg">
              <g clip-path="url(#clip0_1099_14080)">
                <path d="M7.64881 6.50047L12.7619 1.3879C13.0793 1.0705 13.0793 0.555904 12.7619 0.238535C12.4445 -0.0788605 11.9299 -0.0788605 11.6126 0.238535L6.49998 5.35164L1.38741 0.238535C1.07001 -0.0788605 0.555416 -0.0788605 0.238046 0.238535C-0.0793234 0.55593 -0.0793488 1.07053 0.238046 1.3879L5.35115 6.50047L0.238046 11.6131C-0.0793488 11.9305 -0.0793488 12.4451 0.238046 12.7624C0.555442 13.0798 1.07004 13.0798 1.38741 12.7624L6.49998 7.6493L11.6126 12.7624C11.9299 13.0798 12.4445 13.0798 12.7619 12.7624C13.0793 12.445 13.0793 11.9304 12.7619 11.6131L7.64881 6.50047Z" fill="currentColor"/>
              </g>
              <defs>
                <clipPath id="clip0_1099_14080">
                  <rect width="13" height="13" fill="white"/>
                </clipPath>
              </defs>
            </svg>
            <div class="warning-span">Добавление категории</div>
            <span style="font-weight: 550">Название категории</span>
            <input v-model="permCategoryInput" placeholder="Введите название">
            <div style="display: flex; justify-content: center; margin-top: 15px">
              <button @click="addCategory">Добавить</button>
            </div>
          </div>
        </div>
      </Transition>
      <div class="card">
        <h1>Название товара</h1>
        <input class="required" v-model="productName" placeholder="Введите название">
      </div>
      <div class="card">
        <h1>Описание</h1>
        <input class="required" v-model="productDescription" placeholder="Напишите описание">
      </div>
      <div class="card">
        <h1>Артикул</h1>
        <input class="required" id='articleInput' v-model="productArticle" placeholder="Введите артикул">
      </div>
      <div class="card" style="display: flex; justify-content: space-between">
        <div class="block-input">
          <h1>Цена</h1>
          <div class="required">
            <input v-model="productPrice" type="number" placeholder="Цена" style="width: 80%">
            <span>₽</span>
          </div>
        </div>
        <div class="block-input">
          <h1>Кол-во на складе</h1>
          <div class="required" style="width: 100%;">
            <input v-model="productCount" type="number" placeholder="Количество">
            <span>шт.</span>
          </div>
        </div>
      </div>
      <div v-if="isLoading" style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column; font-size: 32px; background-color: var(--app-background-color)">
        <h1 style="font-size: 32px; margin: 10px">Загрузка...</h1>
        <p v-show="this.reasonLoading" style="margin: 10px; text-wrap: wrap; max-width: 80%; text-align: center;">{{reasonLoading}}</p>
      </div>
      <div v-else class="card">
        <h1>Фото товара</h1>
        <div class="upload-image-block">
          <div class="image-preview-block" v-if="imagePreviews && imagePreviews.length>0">
            <swiper
              :slidesPerView="1"
              :scrollbar="{ hide: false }"
              :modules="modules"
              class="swiper-container"
            >
              <swiper-slide v-for="(preview, index) in imagePreviews" :key="index" class="swiper-slide">
                <img v-if="preview.slice(0, 4) === 'blob'" :src="preview" alt="Uploaded image" class="image-preview"/>
                <img v-else-if="this.itemEditData && this.itemEditData.id" :src="`${this.$store.state.api_url}/files/get_file/`+ preview" alt="Uploaded image" class="image-preview"/>
              </swiper-slide>
            </swiper>
            <input type="file" id="images-input" name="avatar" accept="image/png, image/jpeg, .heic, .heif" @change="handleFileUpload"/>
            <svg width="66" height="66" viewBox="0 0 66 66" fill="none" xmlns="http://www.w3.org/2000/svg">
              <g clip-path="url(#clip0_1326_10836)">
                <path d="M35.75 56.375C35.75 57.134 35.134 57.75 34.375 57.75H12.375C5.55225 57.75 0 52.1978 0 45.375V12.375C0 5.55225 5.55225 0 12.375 0H45.375C52.1978 0 57.75 5.55225 57.75 12.375V34.375C57.75 35.134 57.134 35.75 56.375 35.75C55.616 35.75 55 35.134 55 34.375V12.375C55 7.0675 50.6825 2.75 45.375 2.75H12.375C7.0675 2.75 2.75 7.0675 2.75 12.375V35.299L13.2302 24.8187C16.8657 21.1832 23.2072 21.1832 26.8427 24.8187L46.3512 44.4042C46.8875 44.9405 46.8848 45.8123 46.3512 46.3485C46.0817 46.6152 45.7298 46.75 45.3805 46.75C45.0285 46.75 44.6765 46.6153 44.407 46.3458L24.8985 26.763C22.3053 24.1698 17.7733 24.167 15.1772 26.763L2.75 39.1875V45.375C2.75 50.6825 7.0675 55 12.375 55H34.375C35.134 55 35.75 55.616 35.75 56.375ZM46.75 15.125C46.75 18.9172 43.6645 22 39.875 22C36.0855 22 33 18.9172 33 15.125C33 11.3328 36.0855 8.25 39.875 8.25C43.6645 8.25 46.75 11.3328 46.75 15.125ZM44 15.125C44 12.8507 42.1493 11 39.875 11C37.6007 11 35.75 12.8507 35.75 15.125C35.75 17.3993 37.6007 19.25 39.875 19.25C42.1493 19.25 44 17.3993 44 15.125ZM64.625 52.25H55V42.625C55 41.866 54.384 41.25 53.625 41.25C52.866 41.25 52.25 41.866 52.25 42.625V52.25H42.625C41.866 52.25 41.25 52.866 41.25 53.625C41.25 54.384 41.866 55 42.625 55H52.25V64.625C52.25 65.384 52.866 66 53.625 66C54.384 66 55 65.384 55 64.625V55H64.625C65.384 55 66 54.384 66 53.625C66 52.866 65.384 52.25 64.625 52.25Z" fill="#878787"/>
              </g>
              <defs>
                <clipPath id="clip0_1326_10836">
                  <rect width="66" height="66" fill="white"/>
                </clipPath>
              </defs>
            </svg>
          </div>
          <div v-else>
            <input type="file" id="avatar" name="avatar" accept="image/png, image/jpeg, .heic, .heif" @change="handleFileUpload"/>
            <div>
              <svg width="66" height="66" viewBox="0 0 66 66" fill="none" xmlns="http://www.w3.org/2000/svg">
                <g clip-path="url(#clip0_1326_10836)">
                  <path d="M35.75 56.375C35.75 57.134 35.134 57.75 34.375 57.75H12.375C5.55225 57.75 0 52.1978 0 45.375V12.375C0 5.55225 5.55225 0 12.375 0H45.375C52.1978 0 57.75 5.55225 57.75 12.375V34.375C57.75 35.134 57.134 35.75 56.375 35.75C55.616 35.75 55 35.134 55 34.375V12.375C55 7.0675 50.6825 2.75 45.375 2.75H12.375C7.0675 2.75 2.75 7.0675 2.75 12.375V35.299L13.2302 24.8187C16.8657 21.1832 23.2072 21.1832 26.8427 24.8187L46.3512 44.4042C46.8875 44.9405 46.8848 45.8123 46.3512 46.3485C46.0817 46.6152 45.7298 46.75 45.3805 46.75C45.0285 46.75 44.6765 46.6153 44.407 46.3458L24.8985 26.763C22.3053 24.1698 17.7733 24.167 15.1772 26.763L2.75 39.1875V45.375C2.75 50.6825 7.0675 55 12.375 55H34.375C35.134 55 35.75 55.616 35.75 56.375ZM46.75 15.125C46.75 18.9172 43.6645 22 39.875 22C36.0855 22 33 18.9172 33 15.125C33 11.3328 36.0855 8.25 39.875 8.25C43.6645 8.25 46.75 11.3328 46.75 15.125ZM44 15.125C44 12.8507 42.1493 11 39.875 11C37.6007 11 35.75 12.8507 35.75 15.125C35.75 17.3993 37.6007 19.25 39.875 19.25C42.1493 19.25 44 17.3993 44 15.125ZM64.625 52.25H55V42.625C55 41.866 54.384 41.25 53.625 41.25C52.866 41.25 52.25 41.866 52.25 42.625V52.25H42.625C41.866 52.25 41.25 52.866 41.25 53.625C41.25 54.384 41.866 55 42.625 55H52.25V64.625C52.25 65.384 52.866 66 53.625 66C54.384 66 55 65.384 55 64.625V55H64.625C65.384 55 66 54.384 66 53.625C66 52.866 65.384 52.25 64.625 52.25Z" fill="#878787"/>
                </g>
                <defs>
                  <clipPath id="clip0_1326_10836">
                    <rect width="66" height="66" fill="white"/>
                  </clipPath>
                </defs>
              </svg>
              <span>Выбрать файл</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="options" class="options">
      <div style="margin: 10px 0; width: 100%" v-for="(option, index) in options">
        <span style="padding-left: 15px; font-weight: 550">Дополнительная опция №{{index+1}}</span>
        <input style="height: 35px" v-model="option.name" placeholder="Название опции">
        <input v-if="option.type === 'text'" v-model="option.variants[0]" placeholder="Текст">
        <div v-else-if="option.type === 'block'">
          <swiper
            :slidesPerView="4.5"
            :spaceBetween="10"
            :modules="modules"
          >
            <swiper-slide v-for="(block, index) in option.variants"><input v-model="option.variants[index]" placeholder="Текст"></swiper-slide>
          </swiper>
        </div>
        <div v-else-if="option.type === 'priced_block'">
          <swiper
            :slidesPerView="4.5"
            :spaceBetween="10"
            :modules="modules"
          >
            <swiper-slide style="height: 110px; background-color: var(--app-background-color)" v-for="(block, index) in option.variants">
              <div style="display: flex; flex-direction: column">
                <input style="height: 72px" v-model="option.variants[index]" placeholder="Текст">
                <input style="height: 25px" v-model="option.variants_prices[index]" type="number" min="0">
              </div>
            </swiper-slide>
          </swiper>
        </div>
      </div>
    </div>
    <div @click="toggleModelWindow" class="options">
      <svg width="34" height="34" viewBox="0 0 34 34" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g clip-path="url(#clip0_1326_10842)">
          <path d="M17 0C7.62592 0 0 7.62592 0 17C0 26.3741 7.62592 34 17 34C26.3741 34 34 26.3741 34 17C34 7.62592 26.3741 0 17 0ZM17 32.5833C8.40792 32.5833 1.41667 25.5921 1.41667 17C1.41667 8.40792 8.40792 1.41667 17 1.41667C25.5921 1.41667 32.5833 8.40792 32.5833 17C32.5833 25.5921 25.5921 32.5833 17 32.5833ZM24.0833 17C24.0833 17.391 23.766 17.7083 23.375 17.7083H17.7083V23.375C17.7083 23.766 17.391 24.0833 17 24.0833C16.609 24.0833 16.2917 23.766 16.2917 23.375V17.7083H10.625C10.234 17.7083 9.91667 17.391 9.91667 17C9.91667 16.609 10.234 16.2917 10.625 16.2917H16.2917V10.625C16.2917 10.234 16.609 9.91667 17 9.91667C17.391 9.91667 17.7083 10.234 17.7083 10.625V16.2917H23.375C23.766 16.2917 24.0833 16.609 24.0833 17Z" fill="#878787"/>
        </g>
        <defs>
          <clipPath id="clip0_1326_10842">
            <rect width="34" height="34" fill="white"/>
          </clipPath>
        </defs>
      </svg>
      <span style="font-weight: 350; font-size: 12px; margin-top: 5px">Добавить опцию</span>
    </div>
    <Transition>
      <div v-show="modelWindowOptionIsActive" class="model-wrapper">
        <div class="model-window">
          <svg @click="toggleModelWindow" width="13" height="13" viewBox="0 0 13 13" fill="none" xmlns="http://www.w3.org/2000/svg">
            <g clip-path="url(#clip0_1099_14080)">
              <path d="M7.64881 6.50047L12.7619 1.3879C13.0793 1.0705 13.0793 0.555904 12.7619 0.238535C12.4445 -0.0788605 11.9299 -0.0788605 11.6126 0.238535L6.49998 5.35164L1.38741 0.238535C1.07001 -0.0788605 0.555416 -0.0788605 0.238046 0.238535C-0.0793234 0.55593 -0.0793488 1.07053 0.238046 1.3879L5.35115 6.50047L0.238046 11.6131C-0.0793488 11.9305 -0.0793488 12.4451 0.238046 12.7624C0.555442 13.0798 1.07004 13.0798 1.38741 12.7624L6.49998 7.6493L11.6126 12.7624C11.9299 13.0798 12.4445 13.0798 12.7619 12.7624C13.0793 12.445 13.0793 11.9304 12.7619 11.6131L7.64881 6.50047Z" fill="currentColor"/>
            </g>
            <defs>
              <clipPath id="clip0_1099_14080">
                <rect width="13" height="13" fill="white"/>
              </clipPath>
            </defs>
          </svg>
          <div class="warning-span">Выберите вид дополнительной опции</div>
          <div style="color: #878787; padding-left: 15px; padding-bottom: 5px; margin-top: 15px">Текстовая</div>
          <div class="option-block" @click="chooseOption($event.target)">
            <img v-if="tg.colorScheme === 'light'" id="text" src="@/assets/admin-panel/text-option.png" alt="text-option">
            <img v-else id="text" src="@/assets/admin-panel/dark-text-option.png" alt="text-option">
          </div>
          <div style="color: #878787; padding-left: 15px; padding-bottom: 5px; margin-top: 15px">Блочная</div>
          <div class="option-block" @click="chooseOption($event.target)">
            <img v-if="tg.colorScheme === 'light'" id="block" src="@/assets/admin-panel/block-option.png" alt="block-option">
            <img v-else id="block" src="@/assets/admin-panel/dark-block-option.png" alt="block-option">
          </div>
          <div style="color: #878787; padding-left: 15px; padding-bottom: 5px; margin-top: 15px">Размеры (с зависимыми ценами)</div>
          <div class="option-block" @click="chooseOption($event.target)">
            <img v-if="tg.colorScheme === 'light'" id="priced_block" src="@/assets/admin-panel/size-with-price-block.png" alt="priced_block">
            <img v-else id="priced_block" src="@/assets/admin-panel/dark-size-with-price-block.png" alt="priced_block">
          </div>
          <div style="display: flex; justify-content: center; margin-top: 15px">
            <button @click="addOption">Выбрать</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped lang="scss">
*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  font-size: 16px;
  font-weight: 500;
  color: var(--app-text-color);
}

.wrapper {
  transition: opacity 0.5s ease;
  margin: 0 5%;
  height: 100%;
  .header {
    max-width: 100%;
    padding-top: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    span {
      font-size: 20px;
      font-weight: bold;
    }
  }
}

.main {
  .card {
    margin: 5% 0;
    h1 {
      margin: 0 0 5px 15px;
      font-weight: 550;
    }
    input {
      width: 100%;
      height: 48px;
      border-radius: 15px;
      padding-left: 15px;
      background-color: var(--app-card-background-color);
      border: none;

      ::placeholder {
        font-weight: 350;
        color: var(--app-text-color);
        font-size: 16px;
      }
      &:focus {
        outline: 2px solid var(--app-text-color);
        &::placeholder {
          opacity: 0;
        }
      }
    }
    .block-input {
      display: flex;
      flex-direction: column;
      text-align: start;
      div {
        background-color: var(--app-card-background-color);
        width: 80%;
        border-radius: 15px;
        display: flex;
        justify-content: space-around;
        align-items: center;
        input {
          &:focus {
            outline: none;
            border: none;
            &::placeholder {
              opacity: 0;
            }
          }
        }
        span {
          padding-right: 15px;
        }
      }
      h1 {
        margin: 0 0 10px 10px;
      }
    }
  }
}


.category-block {
  background-color: var(--app-card-background-color);
  width: 100%;
  height: 48px;
  border-radius: 15px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
  span {
    font-weight: 350;
  }
}

.upload-image-block {
  height: 358px;
  background-color: var(--app-card-background-color);
  border-radius: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  div {
    display: flex;
    flex-direction: column;
    align-items: center;
    span {
      color: #878787;
      font-size: 13px;
      font-weight: 350;
    }
  }
  input[type=file] {
    outline:0;
    opacity:0;
    user-select:none;
    padding: 0;
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
    cursor: pointer;
    z-index: 1;
  }
}

.image-preview-block {
  width: 100%;
  input[type=file] {
    position: absolute;
    bottom: 0;
    top: auto;
    height: 10%;
  }
  svg {
    position: absolute;
    bottom: 10px;
    width: 23px;
    height: 23px;
  }
}

.image-preview {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 250px;
  height: 250px;
  border-radius: 15px;
  z-index: 2;
  object-fit: cover;
}

.swiper-container {
  width: 90%;
  height: 275px;
  .swiper-slide {
    text-align: center;
    display: flex;
    justify-content: center;
    align-items: center;
  }
}

.swiper-scrollbar{
  background: none;
  .swiper-scrollbar-drag {
    background-color: #59C0F9;
  }
}

.options {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  width: 100%;
  margin: 15px 0;
  svg {
    display: flex;
    align-items: center;
    justify-content: center;
  }
  input {
    width: 100%;
    height: 48px;
    border-radius: 15px;
    padding-left: 15px;
    background-color: var(--app-card-background-color);
    border: none;
    margin: 5px 0 0;
    ::placeholder {
      font-weight: 350;
      color: var(--app-text-color);
      font-size: 16px;
    }
    &:focus {
      outline: 2px solid var(--app-text-color);
      &::placeholder {
        opacity: 0;
      }
    }
  }
  .swiper {
    width: 100%;
    margin-top: 5px;
    .swiper-slide {
      width: 73px;
      height: 64px;
      background-color: var(--app-card-background-color);
      border-radius: 15px;
      display: flex;
      justify-content: center;
      align-items: center;
      input {
        width: 100%;
        border: none;
        text-align: center;
        padding: 0;
        ::placeholder {
          text-align: center;
        }
        &:focus {
          outline: none;
        }
      }
    }
  }
}

.model-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100%;
  background-color: rgb(0, 0, 0, 30%);
  z-index: 10;
  .model-window {
    background-color: var(--app-card-background-color);
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
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
    input {
      background-color: var(--app-background-color);
      width: 100%;
      height: 48px;
      border-radius: 15px;
      padding-left: 15px;
      border: none;
      margin: 5px 0;
      &:focus {
        outline: 2px solid var(--app-text-color);
        &::placeholder {
          opacity: 0;
        }
      }
    }
    svg {
      position: absolute;
      right: 5%;
    }
    img {
      width: 100%;
    }
    button {
      background-color: var(--app-background-color);
      width: 166px;
      height: 37px;
      border-radius: 15px;
      box-shadow: none;
      border: none;
      font-weight: 600;
    }
  }
}

.option-block {
  width: 100%;
  height: 100px;
  border-radius: 15px;
  img {
    width: 100%;
    height: 100%;
  }
}

.chosen {
  border: 3px solid #9EDCFF;
}


.card-footer {
  border-radius: 0 0 15px 15px;
  background-color: var(--app-card-background-color);
  transition: opacity 0.3s ease-in-out;
  padding: 5px 0 15px;
  hr {
    border: 1px solid var(--app-hr-border-color);
    width: 97.5%;
    margin: 0 auto;
  }
  .items-styles {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100%, 1fr));
    grid-column: 1;
    grid-gap: 10px;
    padding: 0;
    .category-item {
      list-style-type: none;
      .category-main {
        width: 100%;
        height: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 15px 10px;
        span {
          color: #878787;
        }
        img {
          width: 12px;
          height: 12px;
        }
      }
    }
  }
}

.red-placeholder::placeholder{
  color: #ff003c;
}
</style>