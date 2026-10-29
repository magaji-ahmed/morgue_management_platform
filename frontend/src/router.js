import { createRouter, createWebHistory } from "vue-router";
import { auth } from "./api";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: () => import("./pages/Login.vue"), meta: { public: true } },
    { path: "/", component: () => import("./pages/Bodies.vue") },
    { path: "/bodies/new", component: () => import("./pages/BodyNew.vue") },
    { path: "/bodies/:id", component: () => import("./pages/BodyDetail.vue") },
    { path: "/users", component: () => import("./pages/Users.vue"), meta: { admin: true } },
    { path: "/services", component: () => import("./pages/Services.vue"), meta: { admin: true } },
    { path: "/account", component: () => import("./pages/Account.vue") },
  ],
});

router.beforeEach((to) => {
  if (to.meta.public) return true;
  if (!auth.token) return "/login";
  if (auth.user?.must_change_password && to.path !== "/account") return "/account";
  if (to.meta.admin && auth.user?.role !== "admin") return "/";
});

export default router;
