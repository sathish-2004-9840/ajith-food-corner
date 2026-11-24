const rupee = n => "₹" + Number(n).toFixed(0);
let menu = [], cart = {}, activeCategory = "All", orderType = "pickup";
const $ = id => document.getElementById(id);

async function loadMenu() {
  try {
    const res = await fetch("/api/menu");
    menu = await res.json();
    renderCategories(); renderMenu();
  } catch { $("menu-grid").innerHTML = '<p class="loading">Could not load the menu. Refresh the page.</p>'; }
}
function renderCategories() {
  const cats = ["All", ...new Set(menu.map(x => x.category))];
  $("categories").innerHTML = cats.map(c => `<button class="category-chip ${c===activeCategory?'active':''}" data-category="${c}">${c}</button>`).join("");
  $("categories").querySelectorAll("button").forEach(b => b.onclick = () => {activeCategory=b.dataset.category;renderCategories();renderMenu();});
}
function renderMenu() {
  const q = $("menu-search").value.toLowerCase();
  const list = menu.filter(x => (activeCategory==="All" || x.category===activeCategory) && (x.name.toLowerCase().includes(q) || x.description.toLowerCase().includes(q)));
  $("menu-grid").innerHTML = list.length ? list.map(item => `
    <article class="food-card"><div class="food-image ${item.category.toLowerCase().replaceAll(' ','-')}"><span>${item.emoji}</span>${item.tag==='popular'?'<b class="food-tag">CUSTOMER FAVOURITE</b>':''}</div>
    <div class="food-info"><div class="food-category">${item.category}</div><h3>${item.name}</h3><p>${item.description}</p>
    <div class="food-bottom"><b>${rupee(item.price)}</b><button class="add-btn" data-add="${item.id}">＋ Add</button></div></div></article>`).join("") : '<p class="loading">No dishes found. Try another search.</p>';
  document.querySelectorAll("[data-add]").forEach(b => b.onclick = () => addItem(Number(b.dataset.add)));
}
function addItem(id) { cart[id]=(cart[id]||0)+1; renderCart(); toast("Added to your order"); }
function changeQty(id, delta) { cart[id]=(cart[id]||0)+delta; if(cart[id]<=0) delete cart[id]; renderCart(); }
function renderCart() {
  const entries = Object.entries(cart);
  const count = entries.reduce((s,[,q])=>s+q,0);
  const subtotal = entries.reduce((s,[id,q])=>s+menu.find(m=>m.id==id).price*q,0);
  const fee = orderType==="delivery" && count ? 30 : 0;
  $("nav-count").textContent=count; $("subtotal").textContent=rupee(subtotal);
  $("delivery-fee").textContent=rupee(fee); $("total").textContent=rupee(subtotal+fee);
  $("checkout-open").disabled=!count;
  $("cart-items").innerHTML = count ? entries.map(([id,q])=>{const item=menu.find(m=>m.id==id);return `<div class="cart-line"><div><b>${item.name}</b><small>${rupee(item.price)} each</small></div><div class="qty-control"><button data-minus="${id}">−</button><span>${q}</span><button data-plus="${id}">＋</button></div></div>`}).join("") : '<div class="empty-cart"><span>🍽️</span><b>Your plate is waiting.</b><small>Add something delicious from the menu.</small></div>';
  document.querySelectorAll("[data-minus]").forEach(b=>b.onclick=()=>changeQty(Number(b.dataset.minus),-1));
  document.querySelectorAll("[data-plus]").forEach(b=>b.onclick=()=>changeQty(Number(b.dataset.plus),1));
}
function toast(msg){$("toast").textContent=msg;$("toast").classList.add("show");setTimeout(()=>$("toast").classList.remove("show"),1800);}
$("menu-search").addEventListener("input",renderMenu);
$("jump-cart").onclick=()=>$("cart-panel").scrollIntoView({behavior:"smooth",block:"center"});
$("checkout-open").onclick=()=>{$("checkout-modal").classList.add("visible");};
$("modal-close").onclick=()=>{$("checkout-modal").classList.remove("visible");};
$("checkout-modal").addEventListener("click",e=>{if(e.target===$("checkout-modal"))$("checkout-modal").classList.remove("visible");});
document.querySelectorAll('input[name="order_type"]').forEach(r=>r.addEventListener("change",()=>{
  orderType=r.value;$("address-label").classList.toggle("hidden",orderType!=="delivery");
  $("address-label").querySelector("textarea").required=orderType==="delivery";renderCart();
}));
$("checkout-form").addEventListener("submit",async e=>{
  e.preventDefault();const form=new FormData(e.target);
  const payload={name:form.get("name"),phone:form.get("phone"),order_type:form.get("order_type"),address:form.get("address"),notes:form.get("notes"),items:Object.entries(cart).map(([id,qty])=>({id:Number(id),qty}))};
  const button=e.target.querySelector("button[type=submit]");button.disabled=true;button.textContent="Placing order...";
  try{
    const res=await fetch("/api/orders",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const data=await res.json();
    if(!res.ok)throw new Error(data.error||"Unable to place order.");
    $("checkout-message").innerHTML=`<div class="success-box"><b>Order received. Thank you!</b><p>Your order code is <strong>${data.order_code}</strong>.</p><p>Save this code to track your order.</p><a href="#track" id="track-link">Track order details</a></div>`;
    cart={};renderCart();e.target.reset();orderType="pickup";$("address-label").classList.add("hidden");
    $("checkout-message").scrollIntoView({behavior:"smooth"});
  }catch(err){$("checkout-message").textContent=err.message;}
  finally{button.disabled=false;button.innerHTML='Place my order <span>→</span>';}
});
loadMenu();
